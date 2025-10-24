# Matrix2MPO Plus

A Python package for Matrix Product Operator (MPO) decomposition using SVD decomposition and various canonical forms for efficient tensor network representations.

## Features

- **MPO Decomposition**: Convert matrices to Matrix Product Operator format
- **SVD-based Decomposition**: Uses Singular Value Decomposition for tensor decomposition
- **Accelerated SVD**: Includes optimized SVD module for faster computation
- **Canonical Forms**: Support for left canonical, right canonical, and mixed canonical forms
- **Truncation**: Built-in support for rank truncation to control compression
- **PyTorch Integration**: Seamless integration with PyTorch tensors
- **Flexible Configuration**: Configurable input/output shapes and truncation parameters
- **Fallback Support**: Automatic fallback to numpy.linalg.svd if accelerated module is unavailable

## Installation

You can install Matrix2MPO Plus using pip:

```bash
pip install matrix2mpo-plus
```

## Quick Start

```python
import numpy as np
import torch
from matrix2mpo_plus import MPO

# Create a sample matrix
matrix = np.random.rand(64, 64)

# Define MPO input and output shapes
mpo_input_shape = [8, 8]  # 8 * 8 = 64
mpo_output_shape = [8, 8]  # 8 * 8 = 64

# Create MPO instance
mpo = MPO(
    mpo_input_shape=mpo_input_shape,
    mpo_output_shape=mpo_output_shape,
    truncate_num=16  # Maximum bond dimension
)

# Convert matrix to MPO format
tensor_set, lambda_set, lambda_set_value = mpo.matrix2mpo(matrix)

# Convert back to matrix
reconstructed_matrix = mpo.mpo2matrix(tensor_set)

# Calculate compression ratio
original_params = matrix.size
mpo_params = mpo.calculate_total_mpo_param()
compression_ratio = original_params / mpo_params

print(f"Original parameters: {original_params}")
print(f"MPO parameters: {mpo_params}")
print(f"Compression ratio: {compression_ratio:.2f}x")
```

## API Reference

### MPO Class

The main class for MPO decomposition operations.

#### Parameters

- `mpo_input_shape` (list): Input dimensions for MPO decomposition
- `mpo_output_shape` (list): Output dimensions for MPO decomposition  
- `truncate_num` (int): Maximum bond dimension for truncation
- `fix_rank` (list, optional): Fixed rank for each bond dimension

#### Methods

- `matrix2mpo(matrix, cutoff=True)`: Convert matrix to MPO format
- `mpo2matrix(tensor_set)`: Convert MPO format back to matrix
- `calculate_total_mpo_param(cutoff=True)`: Calculate total number of parameters
- `test_difference(matrix1, matrix2)`: Calculate difference between two matrices

### Power Iteration SVD

```python
from matrix2mpo_plus import power_iteration_svd

# Compute SVD using power iteration
U, S, Vt = power_iteration_svd(matrix, k=10, max_iter=100)
```

## Requirements

- Python >= 3.7
- NumPy >= 1.19.0
- PyTorch >= 1.8.0

## Performance

This package includes an optimized SVD module (`svd_module`) that provides faster computation compared to standard numpy.linalg.svd. The package automatically detects and uses the accelerated module when available, with graceful fallback to numpy's implementation if needed.

## Development

To run tests:

```bash
pip install -e .[dev]
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use this package in your research, please cite:

```bibtex
@inproceedings{Liu-ACL-2021,
  author    = {Peiyu Liu and
               Ze{-}Feng Gao and
               Wayne Xin Zhao and
               Z. Y. Xie and
               Zhong{-}Yi Lu and
               Ji{-}Rong Wen},
  title     = "Enabling Lightweight Fine-tuning for Pre-trained Language Model Compression
               based on Matrix Product Operators",
  booktitle = {{ACL}},
  year      = {2021},
}
```

## Support

For questions and support, please contact liupeiyustu@163.com.
