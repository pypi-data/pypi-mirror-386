# tfkan/ops/grid.py

import tensorflow as tf

@tf.function
def build_adaptive_grid(
    x: tf.Tensor, 
    grid_size: int, 
    spline_order: int, 
    grid_eps: float = 0.02, 
    margin: float = 0.01,
    dtype: tf.DType = tf.float32
) -> tf.Tensor:
    """
    Construct an adaptive grid based on input tensor quantiles.

    The final grid is a weighted average of a uniform grid and an adaptive grid
    derived from data quantiles. This provides stability while concentrating
    grid points in data-rich regions. This function is compiled into a static
    graph using @tf.function for performance.

    Parameters
    ----------
    x : tf.Tensor
        The input tensor with shape (batch_size, in_size).
    grid_size : int
        The number of intervals in the grid.
    spline_order : int
        The order of the spline.
    grid_eps : float, optional
        The weight for the uniform grid component, ensuring grid point separation. Defaults to 0.02.
    margin : float, optional
        The margin to extend the grid range beyond the min/max of the data. Defaults to 0.01.
    dtype : tf.DType, optional
        The data type for the grid. Defaults to tf.float32.

    Returns
    -------
    tf.Tensor
        The adaptive grid with shape (in_size, grid_size + 2 * spline_order + 1).
    """
    tf.debugging.assert_rank(x, 2, "Input tensor x must be 2D (batch_size, in_size).")
    
    # 1. Adaptive Grid from Quantiles
    x_sorted = tf.sort(x, axis=0)
    total_points = tf.shape(x)[0]
    indices = tf.cast(tf.linspace(0, tf.cast(total_points - 1, dtype), grid_size + 1), tf.int32)
    grid_adaptive = tf.gather(x_sorted, indices, axis=0)  # Shape: (grid_size + 1, in_size)

    # 2. Uniform Grid
    x_min = x_sorted[0, :] - margin
    x_max = x_sorted[-1, :] + margin
    step = (x_max - x_min) / grid_size
    grid_uniform = x_min + tf.range(grid_size + 1, dtype=dtype)[:, None] * step

    # 3. Combine grids
    grid = grid_eps * grid_uniform + (1 - grid_eps) * grid_adaptive

    # 4. Extend grid with exterior knots for B-spline computation
    extended_knots_left = [grid[:1] - step * tf.cast(i, dtype=dtype) for i in range(spline_order, 0, -1)]
    extended_knots_right = [grid[-1:] + step * tf.cast(i, dtype=dtype) for i in range(1, spline_order + 1)]
    
    grid = tf.concat(extended_knots_left + [grid] + extended_knots_right, axis=0)

    # Transpose to (in_size, num_knots)
    grid = tf.transpose(grid)

    return grid