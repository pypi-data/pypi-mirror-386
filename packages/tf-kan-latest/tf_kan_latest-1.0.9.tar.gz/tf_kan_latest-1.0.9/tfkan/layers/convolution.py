# tfkan/layers/convolution.py

import tensorflow as tf
import numpy as np
from keras.layers import Layer
from typing import Tuple, Union, Any
from abc import abstractmethod

from .base import LayerKAN
from .dense import DenseKAN

class ConvolutionKAN(Layer, LayerKAN):
    """
    Abstract base class for KAN convolutional layers.
    """
    def __init__(self,
        rank: int,
        filters: int,
        kernel_size: Any,
        strides: Any,
        padding: str = 'VALID',
        use_bias: bool = True,
        kan_kwargs: dict = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.rank = rank
        self.filters = filters
        self.padding = padding.upper()
        self.use_bias = use_bias
        self.kan_kwargs = kan_kwargs if kan_kwargs is not None else {}

        if not isinstance(kernel_size, (tuple, list)):
            kernel_size = tuple([kernel_size] * self.rank)
        if not isinstance(strides, (tuple, list)):
            strides = tuple([strides] * self.rank)

        if len(kernel_size) != self.rank:
            raise ValueError(f"kernel_size must be of length {self.rank}, but got {len(kernel_size)}")
        if len(strides) != self.rank:
            raise ValueError(f"strides must be of length {self.rank}, but got {len(strides)}")

        self.kernel_size = kernel_size
        self.strides = strides

    def build(self, input_shape: Union[tf.TensorShape, tuple, list]):
        in_channels = int(input_shape[-1])
        self._in_channels = in_channels
        self._in_size = int(np.prod(self.kernel_size) * in_channels)

        self.kernel_kan = DenseKAN(
            units=self.filters,
            dtype=self.dtype,
            use_bias=False,
            **self.kan_kwargs
        )
        self.kernel_kan.build(self._in_size)

        if self.use_bias:
            self.bias = self.add_weight(
                name='bias',
                shape=(self.filters,),
                initializer='zeros',
                trainable=True
            )
        super().build(input_shape)

    def call(self, inputs: tf.Tensor) -> tf.Tensor:
        patches_2d, output_spatial_shape = self._extract_and_reshape_patches(inputs)
        output = self.kernel_kan(patches_2d)
        final_output_shape = tf.concat([output_spatial_shape, [self.filters]], axis=0)
        output = tf.reshape(output, final_output_shape)

        if self.use_bias:
            output += self.bias

        return output

    @abstractmethod
    def _extract_and_reshape_patches(self, inputs: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        raise NotImplementedError

    def update_grid_from_samples(self, inputs: tf.Tensor, **kwargs):
        patches_2d, _ = self._extract_and_reshape_patches(inputs)
        self.kernel_kan.update_grid_from_samples(patches_2d, **kwargs)

    def extend_grid_from_samples(self, inputs: tf.Tensor, extend_grid_size: int, **kwargs):
        patches_2d, _ = self._extract_and_reshape_patches(inputs)
        self.kernel_kan.extend_grid_from_samples(patches_2d, extend_grid_size, **kwargs)

    def get_config(self) -> dict:
        config = super().get_config()
        config.update({
            'rank': self.rank,
            'filters': self.filters,
            'kernel_size': self.kernel_size,
            'strides': self.strides,
            'padding': self.padding,
            'use_bias': self.use_bias,
            'kan_kwargs': self.kan_kwargs
        })
        return config

@tf.keras.utils.register_keras_serializable(package="tfkan")
class Conv1DKAN(ConvolutionKAN):
    """1D KAN convolution layer (e.g., for time series)."""
    def __init__(self, filters, kernel_size, strides=1, padding='VALID', use_bias=True, kan_kwargs=None, **kwargs):
        super().__init__(rank=1, filters=filters, kernel_size=kernel_size, strides=strides, padding=padding, use_bias=use_bias, kan_kwargs=kan_kwargs, **kwargs)

    def _extract_and_reshape_patches(self, inputs: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        # HARDENED: Use the same logic as Conv2D for consistency
        # Add a dummy height dimension, apply 2D patch extraction, and remove it
        inputs_4d = tf.expand_dims(inputs, axis=2) # (batch, steps, 1, channels)
        
        patches = tf.image.extract_patches(
            inputs_4d,
            sizes=[1, self.kernel_size[0], 1, 1],
            strides=[1, self.strides[0], 1, 1],
            rates=[1, 1, 1, 1],
            padding=self.padding
        ) # (batch, out_steps, 1, k_w * 1 * channels)
        
        # Squeeze out the dummy height dimension
        output_spatial_shape = tf.shape(patches)[:2] # (batch, out_steps)
        patches_reshaped = tf.reshape(patches, (-1, self._in_size))
        return patches_reshaped, output_spatial_shape

@tf.keras.utils.register_keras_serializable(package="tfkan")
class Conv2DKAN(ConvolutionKAN):
    """2D KAN convolution layer (e.g., for images). Assumes `channels_last`."""
    def __init__(self, filters, kernel_size, strides=(1, 1), padding='VALID', use_bias=True, kan_kwargs=None, **kwargs):
        super().__init__(rank=2, filters=filters, kernel_size=kernel_size, strides=strides, padding=padding, use_bias=use_bias, kan_kwargs=kan_kwargs, **kwargs)

    def _extract_and_reshape_patches(self, inputs: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        patches = tf.image.extract_patches(
            inputs,
            sizes=[1, *self.kernel_size, 1],
            strides=[1, *self.strides, 1],
            rates=[1, 1, 1, 1],
            padding=self.padding
        )
        output_spatial_shape = tf.shape(patches)[:-1]
        patches_reshaped = tf.reshape(patches, (-1, self._in_size))
        return patches_reshaped, output_spatial_shape

@tf.keras.utils.register_keras_serializable(package="tfkan")
class Conv3DKAN(ConvolutionKAN):
    """3D KAN convolution layer (e.g., for video). Assumes `channels_last`."""
    def __init__(self, filters, kernel_size, strides=(1, 1, 1), padding='VALID', use_bias=True, kan_kwargs=None, **kwargs):
        super().__init__(rank=3, filters=filters, kernel_size=kernel_size, strides=strides, padding=padding, use_bias=use_bias, kan_kwargs=kan_kwargs, **kwargs)

    def _extract_and_reshape_patches(self, inputs: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        patches = tf.extract_volume_patches(
            inputs,
            ksizes=[1, *self.kernel_size, 1],
            strides=[1, *self.strides, 1],
            padding=self.padding
        )
        output_spatial_shape = tf.shape(patches)[:-1]
        patches_reshaped = tf.reshape(patches, (-1, self._in_size))
        return patches_reshaped, output_spatial_shape