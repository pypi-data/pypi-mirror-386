# pixtreme-filter

GPU-accelerated image filtering operations for pixtreme

## Overview

`pixtreme-filter` provides high-performance image filtering operations running on CUDA-enabled GPUs. All operations are optimized for real-time performance and work directly on GPU memory.

## Features

- **Gaussian Blur**: GPU-accelerated Gaussian blur with separable kernels
- **Zero-Copy Operations**: Direct GPU memory processing via CuPy
- **Flexible Interface**: Functional API and class-based API

## Installation

```bash
pip install pixtreme-filter
```

Requires `pixtreme-core` and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_filter as pf
import pixtreme_core as px

# Read image
img = px.imread("input.jpg")

# Apply Gaussian blur
blurred = pf.gaussian_blur(img, ksize=15, sigma=3.0)

# Save result
px.imwrite("output.jpg", blurred)
```

## API

### Gaussian Blur

```python
# Functional API
blurred = pf.gaussian_blur(image, ksize=15, sigma=3.0)

# Class-based API (for repeated operations with same parameters)
blur = pf.GaussianBlur()
blurred = blur.get(image, ksize=15, sigma=3.0)

# Get kernel for custom operations
kernel = pf.get_gaussian_kernel(ksize=15, sigma=3.0)
```

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
