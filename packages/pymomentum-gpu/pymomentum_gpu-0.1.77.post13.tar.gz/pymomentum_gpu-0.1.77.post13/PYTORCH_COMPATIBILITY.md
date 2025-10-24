# PyTorch Compatibility Guide for PyMomentum-GPU

## Overview

`pymomentum-gpu` uses PyTorch's C++ API for tensor operations and GPU acceleration. This creates a dependency on PyTorch's C++ ABI (Application Binary Interface), which can change between PyTorch versions.

## Compatible PyTorch Versions

Each release of `pymomentum-gpu` is built against a specific range of PyTorch versions:

- **Current compatibility**: PyTorch `>=2.8.0,<2.10`
- **Recommended**: PyTorch `2.8.0` or `2.9.x`

## Installation

### Recommended Installation (with compatible PyTorch)

```bash
# Install pymomentum-gpu (will automatically install compatible PyTorch)
pip install pymomentum-gpu

# Or explicitly specify torch version
pip install torch>=2.8.0,<2.10
pip install pymomentum-gpu
```

### Installation with Custom PyTorch Build

If you need a custom PyTorch build (e.g., specific CUDA version):

```bash
# 1. Install your custom PyTorch first (must be 2.8.x or 2.9.x)
pip install torch==2.8.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# 2. Then install pymomentum-gpu
pip install --no-deps pymomentum-gpu  # Skip dependencies
pip install numpy>=1.20.0 scipy>=1.7.0  # Install other dependencies manually
```

## Troubleshooting

### ImportError: undefined symbol

**Symptom:**
```python
>>> import pymomentum.geometry
ImportError: /path/to/pymomentum/geometry.cpython-312-x86_64-linux-gnu.so:
undefined symbol: _ZNK3c106SymInt6sym_neERKS0_
```

**Cause:** PyTorch version mismatch. You're using an incompatible PyTorch version (e.g., 2.10.0 or 2.7.0).

**Solution:**

```bash
# Check your current PyTorch version
python -c "import torch; print(torch.__version__)"

# If it's outside the 2.8.x-2.9.x range, reinstall compatible version
pip install "torch>=2.8.0,<2.10" --force-reinstall
```

### Verifying Installation

After installation, verify everything works:

```python
import torch
import pymomentum.geometry

print(f"PyTorch version: {torch.__version__}")
print(f"PyMomentum installed: {pymomentum.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
```

Expected output (example):
```
PyTorch version: 2.8.0
PyMomentum installed: 0.1.77
CUDA available: True
```

## Why This Matters

### C++ ABI Compatibility

`pymomentum-gpu` is compiled as a C++ extension that links against PyTorch's C++ libraries:
- **libtorch**: Core PyTorch C++ library
- **libc10**: PyTorch's foundational tensor library
- **ATen**: PyTorch's tensor operations

These libraries expose C++ symbols (functions, classes) that change between PyTorch versions. When the ABI changes:
- Old symbols may be removed
- New symbols may be added
- Function signatures may change

### What We Don't Bundle

To keep wheel sizes small (~56MB instead of 2GB+), we:
- ✅ **Don't bundle** PyTorch libraries (libtorch, libc10, etc.)
- ✅ **Don't bundle** CUDA libraries (users have their own)
- ❌ **Do require** compatible PyTorch version to be installed separately

## For Developers

### Building for Different PyTorch Versions

If you're building `pymomentum-gpu` from source:

```bash
# 1. Activate your environment with the target PyTorch version
conda activate myenv
python -c "import torch; print(torch.__version__)"  # Should be 2.8.x or 2.9.x

# 2. Build the wheel
pixi run build_wheel

# 3. The wheel will be compatible with that PyTorch version range
```

### Testing Compatibility

```bash
# Test with PyTorch 2.8.0
pip install torch==2.8.0
pip install dist/pymomentum_gpu-*.whl --force-reinstall
python -c "import pymomentum.geometry; print('✓ PyTorch 2.8.0 works')"

# Test with PyTorch 2.9.0
pip install torch==2.9.0 --force-reinstall
python -c "import pymomentum.geometry; print('✓ PyTorch 2.9.0 works')"
```

### Updating Compatible Version Range

When a new PyTorch version is released:

1. **Test compatibility:**
   ```bash
   pip install torch==2.10.0  # New version
   python -m pytest pymomentum/test/
   ```

2. **If compatible, update `pyproject.toml`:**
   ```toml
   dependencies = [
       "torch>=2.8.0,<2.11",  # Updated range
   ]
   ```

3. **Rebuild and test:**
   ```bash
   pixi run clean_dist
   pixi run build_dist
   pixi run test_installed_wheel
   ```

## Version Compatibility Matrix

| pymomentum-gpu | Compatible PyTorch Versions | Build Environment |
|----------------|----------------------------|-------------------|
| 0.1.x | 2.8.0 - 2.9.x | PyTorch 2.8.0 |
| Future releases | TBD | TBD |

## FAQ

### Q: Why not use PyTorch's Python API only?

**A:** PyMomentum uses PyTorch's C++ API for:
- Better performance (direct tensor manipulation)
- GPU kernel integration
- Seamless C++ ↔ Python interop

### Q: Can I use pymomentum-gpu with PyTorch 2.10.0?

**A:** Not yet. Wait for a new pymomentum-gpu release built against PyTorch 2.10.0, or build from source.

### Q: What about CPU-only PyTorch?

**A:** Use `pymomentum-cpu` instead:
```bash
pip install pymomentum-cpu
```

### Q: How do I know which PyTorch version to use?

**A:** Check the dependency constraint in the installed package:
```bash
pip show pymomentum-gpu | grep Requires
# Output: Requires: torch (>=2.8.0,<2.10), numpy (>=1.20.0), scipy (>=1.7.0)
```

### Q: Can I use multiple PyTorch versions?

**A:** Use virtual environments:
```bash
# Environment 1: PyTorch 2.8
python -m venv venv-torch28
source venv-torch28/bin/activate
pip install torch==2.8.0 pymomentum-gpu

# Environment 2: PyTorch 2.9
python -m venv venv-torch29
source venv-torch29/bin/activate
pip install torch==2.9.0 pymomentum-gpu
```

## Additional Resources

- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
- [PyMomentum Documentation](https://facebookresearch.github.io/momentum/)
- [PyMomentum GitHub](https://github.com/facebookresearch/momentum)
- [Report Issues](https://github.com/facebookresearch/momentum/issues)

## Support

If you encounter compatibility issues:

1. **Check PyTorch version:**
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

2. **Check pymomentum-gpu version:**
   ```bash
   pip show pymomentum-gpu
   ```

3. **Report the issue:**
   - Include both versions
   - Include error message
   - Include platform (Linux/Windows/Mac)
   - Open an issue at: https://github.com/facebookresearch/momentum/issues
