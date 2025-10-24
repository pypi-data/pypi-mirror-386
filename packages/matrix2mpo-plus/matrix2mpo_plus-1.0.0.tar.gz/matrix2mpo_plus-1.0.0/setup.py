#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="matrix2mpo-plus",
    version="1.0.0",
    author="Matrix2MPO Plus Team",
    author_email="matrix2mpo@example.com",
    description="A Python package for Matrix Product Operator (MPO) decomposition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/matrix2mpo-plus",
    packages=find_packages(),
    package_data={
        "matrix2mpo_plus": ["libs/*.so"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    keywords="matrix, mpo, tensor, decomposition, svd, machine learning",
    project_urls={
        "Bug Reports": "https://github.com/your-username/matrix2mpo-plus/issues",
        "Source": "https://github.com/your-username/matrix2mpo-plus",
        "Documentation": "https://matrix2mpo-plus.readthedocs.io/",
    },
)
