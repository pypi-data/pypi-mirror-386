# tfkan/layers/base.py

import tensorflow as tf
from abc import ABC, abstractmethod
from typing import Union

from ..ops.spline import calc_spline_values

class LayerKAN(ABC):
    """
    An abstract mixin class providing core KAN functionality.

    This class is not a Keras Layer itself but provides shared methods
    to concrete KAN layer implementations.
    """
    
    # These attributes are expected to be present in the class that inherits this mixin.
    # This helps with static analysis and code completion.
    grid: tf.Variable
    spline_order: int
    spline_kernel: tf.Variable

    def calc_spline_output(self, inputs: tf.Tensor) -> tf.Tensor:
        """
        Calculates the spline activation output.

        Each input feature is mapped to `out_size` features using a weighted sum
        of B-spline basis functions.

        Parameters
        ----------
        inputs : tf.Tensor
            The input tensor with shape (batch_size, in_size).
        
        Returns
        -------
        tf.Tensor
            The spline output tensor with shape (batch_size, in_size, out_size).
        """
        # Calculate B-spline basis values: (batch_size, in_size, basis_size)
        spline_basis_values = calc_spline_values(inputs, self.grid, self.spline_order)
        
        # Compute spline output via einsum:
        # (batch, in_feature, basis) @ (in_feature, basis, out_feature) -> (batch, in_feature, out_feature)
        spline_out = tf.einsum("bik,iko->bio", spline_basis_values, self.spline_kernel)

        return spline_out

    @abstractmethod
    def update_grid_from_samples(self, inputs: tf.Tensor, margin: float = 0.01, grid_eps: float = 0.01):
        """
        Update the spline grid adaptively based on a batch of input samples.
        """
        raise NotImplementedError

    @abstractmethod
    def extend_grid_from_samples(
        self, 
        inputs: tf.Tensor, 
        extend_grid_size: int,
        margin: float = 0.01,
        grid_eps: float = 0.01,
        l2_reg: float = 0.0,
        fast: bool = True
    ):
        """
        Extend and update the spline grid to a new, larger size.
        """
        raise NotImplementedError