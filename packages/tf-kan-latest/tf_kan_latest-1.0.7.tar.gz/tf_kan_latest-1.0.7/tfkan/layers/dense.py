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

    def build(self, input_shape: Union[tf.TensorShape, tuple, list, int]):
        # This new logic handles both shape objects and integers
        if isinstance(input_shape, int):
            in_size = input_shape
        else:
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
        # Pass the original input_shape to the parent's build method if it's not an int
        if not isinstance(input_shape, int):
            super().build(input_shape)
        else:
            self.built = True # Manually set built if input_shape was an int