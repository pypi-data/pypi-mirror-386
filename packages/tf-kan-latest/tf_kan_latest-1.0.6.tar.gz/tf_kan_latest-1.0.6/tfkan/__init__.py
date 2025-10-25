from . import layers
from . import ops
"""
The `tfkan` Library: Building Smarter Neural Networks in TensorFlow
===================================================================

Welcome to `tfkan`, a TensorFlow 2.19+ implementation of Kolmogorov-Arnold
Networks (KANs). This library provides Keras-native layers that allow you to
build models with learnable activation functions, offering greater expressive
power and interpretability compared to traditional architectures.

The Core Idea: From Simple Wires to Smart Dials
-----------------------------------------------

A traditional neural network (MLP) uses simple, linear connections between
neurons. Think of it as a panel of wires, where each wire has a **resistor** (a
weight, `w`) that can only amplify or reduce a signal (`output = w * input`).

A Kolmogorov-Arnold Network (KAN) replaces each of these simple wires with a
small, programmable **dimmer switch**—a learnable 1D function. This switch can
modify the signal in a complex, non-linear way. This "dimmer switch" is
implemented using a B-spline.

.. image:: https://storage.googleapis.com/gweb-uniblog-publish-prod/original_images/KAN_Fig-1_KAN-vs-MLP.png
   :alt: KAN vs MLP connection
   :align: center

B-Splines: The Flexible Ruler Analogy 📏
---------------------------------------

A B-spline is a mathematical tool for creating smooth, flexible curves. It's the
core technology inside our "smart dimmer switch." Imagine you have a flexible
ruler that you want to shape into a curve. You can do this by placing pegs
(called **knots**) on a board and bending the ruler around them.

Two key hyperparameters control this process:

* ``grid_size`` (Resolution): This is the **number of pegs** you use. A small
    ``grid_size`` creates a simple, coarse curve. A large ``grid_size`` allows
    for a much more detailed and intricate curve, capturing finer patterns.

* ``spline_order`` (Smoothness): This is the **physical property of the ruler**
    itself. An order of 1 (linear) results in a pointy curve. An order of 3
    (cubic) creates a perfectly smooth curve and is the most common choice.

In ``tfkan``, every connection in a KAN layer is one of these learnable B-spline
curves. The network learns the best shape for each curve by adjusting its
parameters.

Library Implementation
----------------------

The library is structured into two main parts: the "engine room" (``ops``) and
the user-facing "building blocks" (``layers``).

**1. The `ops` Submodule (The Engine Room ⚙️)**

This submodule contains the low-level, high-performance mathematical functions,
compiled with ``@tf.function`` for speed.

* ``ops.spline``: Contains functions for creating and fitting the B-spline
    curves using the Cox-de Boor algorithm.
* ``ops.grid``: Handles the adaptive grid functionality, allowing the network
    to concentrate knots in data-rich regions for more efficient learning.

**2. The `layers` Submodule (The Keras Building Blocks 🧱)**

These are the ``tf.keras.layers.Layer`` modules that you will use to build models.

* ``layers.DenseKAN``: The fundamental KAN building block, analogous to Keras's
    ``Dense`` layer. Instead of a single weight matrix ``W``, it learns a grid of
    B-spline functions.

* ``layers.Conv1DKAN``, ``layers.Conv2DKAN``, ``layers.Conv3DKAN``: These layers
    cleverly reduce the convolution operation to a dense one. They work by:
    1.  Extracting all possible patches from the input tensor.
    2.  Unrolling and stacking these patches into a giant 2D matrix.
    3.  Processing this matrix in one go with a single, powerful ``DenseKAN``
        layer.
    4.  Reshaping the result back to the appropriate output shape.

This approach is highly efficient and reuses the core ``DenseKAN`` logic.

Quickstart Example
------------------

Using ``tfkan`` layers is as simple as using standard Keras layers. You can mix
and match them to create powerful hybrid models.

.. code-block:: python

    import tensorflow as tf
    from tfkan.layers import Conv2DKAN, DenseKAN

    # Build a hybrid model for image classification
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(32, 32, 3)),

        # Start with a standard Conv2D layer
        tf.keras.layers.Conv2D(32, kernel_size=3, activation='relu'),
        tf.keras.layers.MaxPooling2D(),

        # Follow with a Conv2DKAN layer.
        # Pass KAN-specific args via `kan_kwargs`.
        Conv2DKAN(
            filters=64,
            kernel_size=3,
            kan_kwargs={'grid_size': 8, 'spline_order': 3}
        ),
        tf.keras.layers.GlobalAveragePooling2D(),

        # Use a DenseKAN layer for the main feature transformation
        DenseKAN(units=128, grid_size=5),

        # End with a standard Dense layer for classification
        tf.keras.layers.Dense(units=10)
    ])

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )

    model.summary()

Thanks to the modern Keras serialization protocol, models built with ``tfkan``
layers can be saved and loaded directly with ``model.save()`` and
``tf.keras.models.load_model()``, no custom objects required.
"""

from . import layers
from . import ops

__version__ = "1.0.0"

__all__ = ["layers", "ops"]
__version__ = "1.0.0"

__all__ = ["layers", "ops"]