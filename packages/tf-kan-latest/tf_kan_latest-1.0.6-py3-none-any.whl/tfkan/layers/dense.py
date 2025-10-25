# tfkan/layers/dense.py

import tensorflow as tf
from tensorflow.keras.layers import Layer
from typing import Tuple, List, Union, Callable

from .base import LayerKAN
from ..ops.spline import fit_spline_coef
from ..ops.grid import build_adaptive_grid

@tf.keras.utils.register_keras_serializable(package="tfkan")
class DenseKAN(Layer, LayerKAN):
    """
    A Kolmogorov-Arnold Network layer implemented as a dense, fully connected layer.

    This layer replaces the standard linear transformation `Wx + b` with a sum of
    learnable 1D functions (splines) and a residual basis function:
    `output_j = sum_i( scale_{ij} * (spline_{ij}(x_i) + basis(x_i)) ) + bias_j`

    Attributes:
        units (int): The number of output units.
        grid_size (int): The number of intervals for the spline grid.
        spline_order (int): The order of the B-spline basis functions.
        # ... and other constructor arguments.
    """
    def __init__(
        self,
        units: int,
        use_bias: bool = True,
        grid_size: int = 5,
        spline_order: int = 3,
        grid_range: Union[Tuple[float, float], List[float]] = (-1.0, 1.0),
        spline_initialize_stddev: float = 0.1,
        basis_activation: Union[str, Callable] = tf.keras.activations.silu,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.units = units
        self.use_bias = use_bias
        self.grid_size = grid_size
        self.spline_order = spline_order
        self.grid_range = tuple(grid_range)
        self.spline_initialize_stddev = spline_initialize_stddev
        self.basis_activation_config = tf.keras.activations.serialize(basis_activation)
        self.basis_activation = tf.keras.activations.get(basis_activation)

    def build(self, input_shape: Union[tf.TensorShape, tuple, list]):
        in_size = int(input_shape[-1])
        self.in_size = in_size
        self.spline_basis_size = self.grid_size + self.spline_order
        bound = self.grid_range[1] - self.grid_range[0]

        # Initialize a non-trainable grid variable
        grid_knots = tf.linspace(
            self.grid_range[0] - self.spline_order * bound / self.grid_size,
            self.grid_range[1] + self.spline_order * bound / self.grid_size,
            self.grid_size + 2 * self.spline_order + 1
        )
        grid_knots = tf.repeat(grid_knots[None, :], in_size, axis=0)
        self.grid = tf.Variable(
            initial_value=tf.cast(grid_knots, dtype=self.dtype),
            trainable=False,
            name="spline_grid"
        )

        # Trainable spline coefficients
        self.spline_kernel = self.add_weight(
            name="spline_kernel",
            shape=(self.in_size, self.spline_basis_size, self.units),
            initializer=tf.keras.initializers.RandomNormal(stddev=self.spline_initialize_stddev),
            trainable=True,
        )

        # Trainable scaling factors for the activations
        self.scale_factor = self.add_weight(
            name="scale_factor",
            shape=(self.in_size, self.units),
            initializer=tf.keras.initializers.GlorotUniform(),
            trainable=True,
        )

        if self.use_bias:
            self.bias = self.add_weight(
                name="bias",
                shape=(self.units,),
                initializer=tf.keras.initializers.Zeros(),
                trainable=True,
            )
        super().build(input_shape)

    def call(self, inputs: tf.Tensor) -> tf.Tensor:
        # Reshape inputs to 2D (batch, in_size) and get original shape for restoration
        inputs_2d, orig_shape = self._check_and_reshape_inputs(inputs)
        output_spatial_shape = tf.shape(inputs)[:-1]

        # 1. Spline part: phi_spline(x)
        spline_out = self.calc_spline_output(inputs_2d)  # (batch, in_size, units)

        # 2. Basis part: phi_basis(x)
        basis_out = self.basis_activation(inputs_2d) # (batch, in_size)
        
        # 3. Combine: scale * (spline(x) + basis(x))
        activations = spline_out + tf.expand_dims(basis_out, axis=-1)
        scaled_activations = activations * self.scale_factor

        # 4. Aggregate over input dimension and reshape
        output = tf.reduce_sum(scaled_activations, axis=1) # (batch, units)
        
        if self.use_bias:
            output += self.bias

        # Reshape back to original spatial dimensions + new feature dimension
        final_output_shape = tf.concat([output_spatial_shape, [self.units]], axis=0)
        return tf.reshape(output, final_output_shape)

    def _check_and_reshape_inputs(self, inputs: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        shape = tf.shape(inputs)
        tf.debugging.assert_greater_equal(
            tf.rank(inputs), 2, "Input rank must be at least 2."
        )
        tf.debugging.assert_equal(
            shape[-1], self.in_size, f"Input last dim must be {self.in_size}."
        )
        
        orig_shape = shape[:-1]
        # Reshape to (batch_size, in_size)
        inputs_reshaped = tf.reshape(inputs, (-1, self.in_size))
        return inputs_reshaped, orig_shape

    def update_grid_from_samples(self, inputs: tf.Tensor, margin: float = 0.01, grid_eps: float = 0.01):
        inputs_2d, _ = self._check_and_reshape_inputs(inputs)
        current_spline_out = self.calc_spline_output(inputs_2d)

        new_grid = build_adaptive_grid(inputs_2d, self.grid_size, self.spline_order, grid_eps, margin, self.dtype)
        updated_kernel = fit_spline_coef(inputs_2d, current_spline_out, new_grid, self.spline_order)

        self.grid.assign(new_grid)
        self.spline_kernel.assign(updated_kernel)

    def extend_grid_from_samples(self, inputs: tf.Tensor, extend_grid_size: int, **kwargs):
        if extend_grid_size <= self.grid_size:
            raise ValueError(f"extend_grid_size must be > current grid_size ({self.grid_size}).")

        inputs_2d, _ = self._check_and_reshape_inputs(inputs)
        current_spline_out = self.calc_spline_output(inputs_2d)
        
        new_grid = build_adaptive_grid(inputs_2d, extend_grid_size, self.spline_order, **kwargs)
        updated_kernel = fit_spline_coef(inputs_2d, current_spline_out, new_grid, self.spline_order)

        # Re-create weights and grid with new dimensions
        self.grid_size = extend_grid_size
        self.spline_basis_size = extend_grid_size + self.spline_order
        
        self.grid.assign(new_grid)
        # We need to recreate the kernel with the new shape
        self.spline_kernel = self.add_weight(
            name="spline_kernel",
            shape=(self.in_size, self.spline_basis_size, self.units),
            initializer=tf.keras.initializers.Constant(updated_kernel),
            trainable=True,
        )


    def get_config(self) -> dict:
        config = super().get_config()
        config.update({
            "units": self.units,
            "use_bias": self.use_bias,
            "grid_size": self.grid_size,
            "spline_order": self.spline_order,
            "grid_range": self.grid_range,
            "spline_initialize_stddev": self.spline_initialize_stddev,
            "basis_activation": self.basis_activation_config
        })
        return config