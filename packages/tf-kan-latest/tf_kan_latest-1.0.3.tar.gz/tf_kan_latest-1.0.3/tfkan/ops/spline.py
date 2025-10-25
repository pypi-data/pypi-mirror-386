# tfkan/ops/spline.py

import tensorflow as tf

@tf.function
def calc_spline_values(x: tf.Tensor, grid: tf.Tensor, spline_order: int) -> tf.Tensor:
    """
    Calculate B-spline basis values using the Cox-de Boor recursion formula.

    This function is compiled into a static graph using @tf.function for performance.

    Parameters
    ----------
    x : tf.Tensor
        The input tensor with shape (batch_size, in_size).
    grid : tf.Tensor
        The grid tensor (knots) with shape (in_size, grid_size + 2 * spline_order + 1).
    spline_order : int
        The order of the spline (e.g., 3 for cubic splines).

    Returns
    -------
    tf.Tensor
        B-spline basis tensor of shape (batch_size, in_size, grid_size + spline_order).
    """
    # Ensure input is 2D and add a dimension for broadcasting
    tf.debugging.assert_rank(x, 2, "Input tensor x must be 2D (batch_size, in_size).")
    x = tf.expand_dims(x, axis=-1)

    # Initialize order-0 B-spline bases (piecewise constant)
    bases = tf.cast(
        tf.logical_and(x >= grid[:, :-1], x < grid[:, 1:]), x.dtype
    )

    # Iteratively compute higher-order B-splines
    for k in range(1, spline_order + 1):
        # Denominators for the recursion formula, with epsilon for numerical stability
        den1 = grid[:, k:-1] - grid[:, :-(k + 1)] + tf.keras.backend.epsilon()
        den2 = grid[:, k + 1:] - grid[:, 1:(-k)] + tf.keras.backend.epsilon()

        term1 = (x - grid[:, :-(k + 1)]) / den1 * bases[:, :, :-1]
        term2 = (grid[:, k + 1:] - x) / den2 * bases[:, :, 1:]
        
        bases = term1 + term2

    return bases

@tf.function
def fit_spline_coef(
    x: tf.Tensor, 
    y: tf.Tensor, 
    grid : tf.Tensor, 
    spline_order: int,
    l2_reg: float = 0.0,
    fast: bool = True
) -> tf.Tensor:
    """
    Fit spline coefficients using linear least squares.

    This function is compiled into a static graph using @tf.function for performance.
    It solves the equation Y = B @ coef for `coef`, where B are the B-spline bases.

    Parameters
    ----------
    x : tf.Tensor
        The spline input tensor with shape (batch_size, in_size).
    y : tf.Tensor
        The target spline output tensor with shape (batch_size, in_size, out_size).
    grid : tf.Tensor
        The spline grid tensor with shape (in_size, grid_size + 2 * spline_order + 1).
    spline_order : int
        The spline order.
    l2_reg : float, optional
        The L2 regularization factor for the least squares solver, by default 0.0.
    fast : bool, optional
        Whether to use the fast solver for the least square problem, by default True.
    
    Returns
    -------
    tf.Tensor
        The solved spline coefficients tensor with shape (in_size, grid_size + spline_order, out_size).
    """
    # Evaluate the B-spline bases B(x)
    # B has shape (batch_size, in_size, grid_size + spline_order)
    B = calc_spline_values(x, grid, spline_order)
    
    # Transpose for batch solving: (in_size, batch_size, ...)
    B = tf.transpose(B, perm=[1, 0, 2])
    y = tf.transpose(y, perm=[1, 0, 2])

    # Solve the linear system for coefficients
    # coef has shape (in_size, grid_size + spline_order, out_size)
    coef = tf.linalg.lstsq(B, y, l2_regularizer=l2_reg, fast=fast)

    return coef