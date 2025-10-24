# PyPI Publishing Guide for pymomentum-gpu

This guide explains how to publish the `pymomentum-gpu` package (GPU-accelerated version with CUDA support) to PyPI.

## Overview

The `pymomentum-gpu` package is a GPU-accelerated distribution with CUDA support. It uses:

1. **`pyproject.toml`** - Package metadata and build configuration (configured for GPU variant)
2. **`pixi.toml`** - Local development and publishing tasks (includes `build_wheel`)
3. **`.github/workflows/publish_to_pypi_gpu.yml`** - Automated GitHub Actions workflow for GPU package

## Key Differences from CPU Package

- **Package Name:** `pymomentum-gpu` (vs `pymomentum`)
- **Dependencies:** Includes `torch>=2.0.0` with CUDA support
- **Build Requirements:** Requires CUDA toolkit (12.9.0) for wheel building
- **Platforms:** Linux and Windows only (macOS does not support CUDA)
- **Python Versions:** 3.12 and 3.13

## Prerequisites for Automated Publishing

### 1. PyPI Trusted Publishing Setup

1. **Create/access the PyPI project:**
   - Go to https://pypi.org
   - Create the `pymomentum-gpu` project if it doesn't exist

2. **Configure Trusted Publishing on PyPI:**
   - Navigate to your project → "Publishing" settings
   - Add a new "Trusted Publisher"
   - Configure:
     - **Owner:** `facebookresearch`
     - **Repository:** `momentum`
     - **Workflow:** `publish_to_pypi_gpu.yml`
     - **Environment:** `pypi-gpu`

3. **Configure GitHub environment:**
   - In GitHub repository: Settings → Environments
   - Create environment named `pypi-gpu`
   - (Optional) Add protection rules

### 2. CUDA Toolkit

The GitHub Actions workflow automatically installs CUDA 12.9.0. For local builds, you need:

```bash
# Linux
# Install CUDA toolkit from NVIDIA's website or use your package manager

# Check CUDA installation
nvcc --version
```

## Automated Publishing via GitHub Actions

### Publishing a New GPU Release

1. **Tag format:** Use `-gpu` suffix for GPU releases
   ```bash
   git tag v0.1.0-gpu
   git push origin v0.1.0-gpu
   ```

2. **Monitor the workflow:**
   - Go to Actions → "Publish pymomentum-gpu to PyPI"
   - The workflow will:
     - Build GPU-enabled wheels for Linux and Windows
     - Build wheels for Python 3.12 and 3.13
     - Create source distribution
     - Publish to PyPI

### Testing Before Release

Test the GPU workflow on TestPyPI:

1. **Manually trigger the workflow:**
   - Go to Actions → "Publish pymomentum-gpu to PyPI"
   - Click "Run workflow"
   - Check "Publish to TestPyPI instead of PyPI"
   - Click "Run workflow"

2. **Test the published package:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ pymomentum-gpu
   ```

## Local Testing and Publishing

### Build GPU Wheel Locally

**Important:** Your system must have CUDA toolkit installed.

```bash
# Clean old artifacts
pixi run clean_dist

# Build GPU wheel using the py312-cuda129 environment
pixi run -e py312-cuda129 build_wheel
```

This builds the wheel directly from `/home/jeongseok/dev/momentum/momentum/pyproject.toml` which is configured for the GPU variant (`pymomentum-gpu`).

### Full Local Verification

```bash
# 1. Clean artifacts
pixi run clean_dist

# 2. Build GPU wheel
pixi run -e py312-cuda129 build_wheel

# 3. Check the distribution
pixi run check_dist

# 4. List built files
ls -lh dist/
```

### Local Publishing

#### To TestPyPI

```bash
pixi run publish_test
```

Configure `~/.pypirc`:
```ini
[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

#### To Production PyPI

```bash
pixi run publish_pypi
```

Configure `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE
```

## Build Configuration Details

### CMake Arguments (from pyproject-gpu.toml)

```cmake
-DBUILD_SHARED_LIBS=OFF
-DMOMENTUM_BUILD_PYMOMENTUM=ON
-DMOMENTUM_BUILD_EXAMPLES=OFF
-DMOMENTUM_BUILD_TESTING=ON
```

### Python Dependencies

The GPU package includes:
- `numpy>=1.20.0`
- `scipy>=1.7.0`
- `torch>=2.0.0` (GPU-enabled, includes CUDA by default when installed from PyPI)

## Version Management

The package uses `setuptools-scm` for automatic version detection from git tags:

- **On tag:** `v0.1.0-gpu` → package version `0.1.0`
- **Between tags:** Uses post-release versioning

To check what version will be built:
```bash
python -c "from setuptools_scm import get_version; print(get_version())"
```

## Complete Publishing Workflow Example

Here's the recommended workflow for publishing a new GPU release:

```bash
# 1. Ensure you're on the latest master
git checkout master
git pull origin master

# 2. Test build locally
pixi run -e py312-cuda129 clean_dist
pixi run -e py312-cuda129 build_wheel_gpu
pixi run check_dist

# 3. Test on TestPyPI (via GitHub Actions)
# Go to Actions → Run "Publish pymomentum-gpu to PyPI" workflow manually
# with "Publish to TestPyPI" option checked

# 4. Verify TestPyPI package
pip install --index-url https://test.pypi.org/simple/ pymomentum-gpu
python -c "import pymomentum; print(pymomentum.__version__)"

# 5. If everything works, create and push the GPU tag
git tag v0.1.0-gpu
git push origin v0.1.0-gpu

# 6. Monitor the automatic publishing workflow in GitHub Actions
```

## Troubleshooting

### CUDA Not Found

**Error:** `CUDA toolkit not found during build`

**Solution:**
- Install CUDA toolkit 12.9.0 or compatible version
- Ensure `nvcc` is in your PATH
- Set `CUDA_HOME` environment variable if needed

### PyTorch CUDA Compatibility

The GPU package depends on PyTorch with CUDA support. When users install `pymomentum-gpu`:

```bash
pip install pymomentum-gpu
```

PyTorch will automatically include CUDA binaries (this is PyTorch's default behavior when installing from PyPI).

### Wheel Naming

Built wheels will have names like:
- `pymomentum_gpu-0.1.0-cp312-cp312-linux_x86_64.whl`
- `pymomentum_gpu-0.1.0-cp313-cp313-win_amd64.whl`

The package name will be `pymomentum-gpu` on PyPI (hyphens), but wheel filenames use underscores.

### Platform Support

**Supported:** Linux (x86_64), Windows (amd64)
**Not Supported:** macOS (no CUDA support), ARM platforms

Users on unsupported platforms should use `pymomentum` or `pymomentum-cpu` instead.

## Testing GPU Functionality

After installation, verify GPU support:

```python
import torch
import pymomentum

# Check CUDA availability
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")

# Test GPU operations with pymomentum
# (Add specific pymomentum GPU tests here)
```

## Best Practices

1. **Always test on TestPyPI first** before production release
2. **Use `-gpu` suffix for tags** to distinguish from CPU releases
3. **Verify CUDA functionality** after building wheels
4. **Document GPU requirements** in package README
5. **Test on both Linux and Windows** if possible
6. **Check wheel size** - GPU wheels will be larger due to dependencies

## Additional Resources

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [CUDA Toolkit Documentation](https://docs.nvidia.com/cuda/)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)
- [scikit-build-core Documentation](https://scikit-build-core.readthedocs.io/)
