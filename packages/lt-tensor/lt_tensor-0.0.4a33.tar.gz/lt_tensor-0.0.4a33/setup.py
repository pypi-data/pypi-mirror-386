from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    version="0.0.4a33",
    name="lt-tensor",
    description="General utilities for PyTorch and others. Built for general use.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gr1336/lt-tensor/",
    install_requires=[
        "torch>=2.6.0",
        "torchaudio>=2.6.0",
        "numpy>=1.26.4",
        "tokenizers",
        "pyyaml",
        "numba",
        "lt-utils>=0.2.0",
        "librosa>=0.10.2.post1,<1",
        "einops",
        "plotly",
        "scipy",
        "typing_extensions",
        "optuna",
        "tqdm",
    ],
    author="gr1336",
    license="Apache Software License (Apache-2.0)",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
)
