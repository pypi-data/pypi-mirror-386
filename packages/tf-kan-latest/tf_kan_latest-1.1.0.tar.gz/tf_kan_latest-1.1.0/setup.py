from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tf-kan-latest",
    version="1.1.0",  # Start with an initial version
    author="Sathyasubrahmanya v S",
    author_email="sathyapel0005@gmail.com",
    description="A Keras-native implementation of Kolmogorov-Arnold Networks (KANs) for TensorFlow.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sathyasubrahmanya/tf-kan",  # Link to your GitHub repo
    packages=find_packages(),
   classifiers=[
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    #"Framework :: TensorFlow", # This is the correct classifier
],
    python_requires=">=3.8",
    install_requires=[
        "tensorflow>=2.16.0", # Specify a minimum TF version
        "numpy>=1.23.0",
    ],
    keywords="tensorflow, keras, kan, kolmogorov-arnold, neural-networks, machine-learning",
)