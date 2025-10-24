# PyTorch Version Compatibility Fix

## Problem

Users installing `pymomentum-gpu` from PyPI encountered this error:

```python
>>> import pymomentum.geometry
ImportError: undefined symbol: _ZNK3c106SymInt6sym_neERKS0_
```

**Root Cause:**
- Wheels were built against PyTorch 2.8.0
- Users installed PyTorch 2.9.0 or newer
- PyTorch's C++ ABI changed between versions, causing symbol mismatches
- The dependency constraint `torch>=2.0.0` was too broad

## Solution Implemented

### 1. Updated `pyproject.toml`

**Changed from:**
```toml
dependencies = [
    "torch>=2.0.0",
]
```

**Changed to:**
```toml
dependencies = [
    "torch>=2.8.0,<2.10",
]
```

This ensures pip installs a compatible PyTorch version automatically.

### 2. Updated `pixi.toml`

**Improvements:**
- ✅ Added proper task dependencies
- ✅ Implemented smart caching (skip rebuild if artifacts exist)
- ✅ Added `publish_pypi_force` task with `--skip-existing` flag
- ✅ All tasks now chain automatically

**New workflow:**
```bash
pixi run publish_pypi  # Does everything: build → repair → check → publish
```

### 3. Documentation

Created comprehensive guides:

- **`PYPI_PUBLISHING_GUIDE.md`** - For maintainers/developers
  - Publishing workflow
  - Task dependencies
  - Caching behavior
  - Troubleshooting

- **`PYTORCH_COMPATIBILITY.md`** - For end users
  - Compatibility matrix
  - Installation instructions
  - Troubleshooting steps
  - FAQ

## Next Steps for Users

### If you're experiencing the symbol error:

```bash
# 1. Check your PyTorch version
python -c "import torch; print(torch.__version__)"

# 2. If it's 2.9.0 or newer, downgrade OR wait for new pymomentum-gpu release
pip install "torch>=2.8.0,<2.10" --force-reinstall

# 3. Reinstall pymomentum-gpu
pip install pymomentum-gpu --force-reinstall

# 4. Verify
python -c "import pymomentum.geometry; print('Success!')"
```

### If you're installing fresh:

```bash
# Just install - pip will handle compatible versions
pip install pymomentum-gpu

# This automatically installs torch>=2.8.0,<2.10
```

## Next Steps for Maintainers

### Immediate: Publish New Wheel

1. **Clean and rebuild with the updated constraint:**
   ```bash
   pixi run clean_dist
   pixi run build_dist
   ```

2. **Verify the wheel metadata:**
   ```bash
   unzip -p dist/pymomentum_gpu-*.whl pymomentum_gpu-*.dist-info/METADATA | grep -A5 "Requires-Dist"
   ```

   Should show:
   ```
   Requires-Dist: torch (>=2.8.0,<2.10)
   ```

3. **Test locally:**
   ```bash
   # Create fresh venv
   python -m venv test_env
   source test_env/bin/activate

   # Install wheel
   pip install dist/pymomentum_gpu-*-manylinux*.whl

   # Verify PyTorch version
   python -c "import torch; print(torch.__version__)"  # Should be 2.8.x or 2.9.x

   # Test import
   python -c "import pymomentum.geometry; print('Success!')"
   ```

4. **Publish to PyPI:**
   ```bash
   # Publish new version
   pixi run publish_pypi
   ```

### Long-term: Monitor PyTorch Releases

When PyTorch 2.10.0 is released:

1. **Test compatibility:**
   ```bash
   pip install torch==2.10.0
   python -m pytest pymomentum/test/
   ```

2. **If compatible, update `pyproject.toml`:**
   ```toml
   dependencies = [
       "torch>=2.8.0,<2.11",  # Expanded range
   ]
   ```

3. **Rebuild and publish:**
   ```bash
   pixi run clean_dist
   pixi run build_dist
   pixi run publish_pypi
   ```

## Testing the Fix

### Test Case 1: Fresh Install with PyTorch 2.8.0

```bash
python -m venv test1
source test1/bin/activate
pip install torch==2.8.0
pip install pymomentum-gpu
python -c "import pymomentum.geometry; print('✓ Works with PyTorch 2.8.0')"
```

### Test Case 2: Fresh Install with PyTorch 2.9.0

```bash
python -m venv test2
source test2/bin/activate
pip install torch==2.9.0
pip install pymomentum-gpu
python -c "import pymomentum.geometry; print('✓ Works with PyTorch 2.9.0')"
```

### Test Case 3: Fresh Install (auto-resolves PyTorch)

```bash
python -m venv test3
source test3/bin/activate
pip install pymomentum-gpu  # Should auto-install compatible torch
python -c "import torch; print(f'Auto-installed: {torch.__version__}')"
python -c "import pymomentum.geometry; print('✓ Works')"
```

### Test Case 4: Incompatible PyTorch (should fail during install)

```bash
python -m venv test4
source test4/bin/activate
pip install torch==2.10.0  # Hypothetical future version
pip install pymomentum-gpu  # Should give dependency resolution error
```

Expected error:
```
ERROR: Cannot install pymomentum-gpu because these package versions have incompatible dependencies.
The conflict is caused by:
    pymomentum-gpu X.Y.Z depends on torch<2.10 and >=2.8.0
```

## Summary

- ✅ Root cause identified: PyTorch C++ ABI incompatibility
- ✅ Fix implemented: Version constraint `torch>=2.8.0,<2.10`
- ✅ Build system improved: Task dependencies and caching
- ✅ Documentation created: Publishing guide and compatibility guide
- ⏳ Next: Rebuild and publish new wheel with fixed constraint

## Files Changed

1. **`pyproject.toml`** - Updated torch dependency constraint
2. **`pixi.toml`** - Improved task dependencies and caching
3. **`PYPI_PUBLISHING_GUIDE.md`** - NEW - Developer guide
4. **`PYTORCH_COMPATIBILITY.md`** - NEW - User guide
5. **`PYTORCH_VERSION_FIX.md`** - NEW - This file

## Questions Answered

### Q1: Do we still need to bundle torch binaries?
**A:** No - you're already NOT bundling them correctly. The `--exclude` flags in `auditwheel` are working as intended.

### Q2: Can we force publish when the same version is already published?
**A:** PyPI doesn't allow overwriting. Solutions:
- Use `publish_pypi_force` (skips existing files)
- Bump version with git tags
- Use TestPyPI for testing

### Q3: Can we improve task dependencies?
**A:** Done! All tasks now have proper dependencies and caching. Just run `pixi run publish_pypi`.
