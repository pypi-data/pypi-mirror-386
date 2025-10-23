"""
Setup script for nthuku-fast package
"""

from setuptools import setup, find_packages
import os

# Read README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

setup(
    name="nthuku_fast",
    version="0.1.2",
    author="Nthuku Team",
    author_email="",
    description="Efficient Multimodal Vision-Language Model with MoE Architecture",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/elijahnzeli1/Nthuku-fast_v2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "tqdm",
        "Pillow",
        "torchvision",
        "numpy",
        "safetensors",
        "kagglehub",
        "pandas",
        "datasets",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
            "mypy",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
