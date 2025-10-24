# PyPI Publishing Guide for pymomentum-gpu

## Quick Answers to Your Questions

### 1. Do we still need to bundle torch binaries?

**NO** - You're already correctly NOT bundling torch binaries!

Looking at your `repair_wheel` task in pixi.toml, you're excluding PyTorch libraries:
```toml
--exclude 'libtorch*.so' --exclude 'libc10*.so'
```

This is the correct approach because:
- `torch>=2.8.0,<2.10` is listed as a dependency in `pyproject.toml`
- Users will install torch separately: `pip install pymomentum-gpu torch`
- This keeps your wheel small (~56MB instead of 2GB+)
- **HOWEVER**: Users must install a compatible PyTorch version (2.8.x or 2.9.x) due to C++ ABI compatibility

**Important ABI Compatibility Note:**
- The wheel is compiled against PyTorch's C++ API, creating ABI dependencies
- PyTorch's C++ ABI can change between versions (e.g., 2.8.x → 2.9.x → 2.10.x)
- The `torch>=2.8.0,<2.10` constraint in `pyproject.toml` ensures users install a compatible version
- If you see `ImportError: undefined symbol` errors, it means PyTorch version mismatch

### 2. Force publishing when the same version exists

PyPI **does not allow** overwriting published versions by design. Your options:

**For Dev Versions (between git tags):**
- ✅ **NEW:** Dev versions now include timestamps (e.g., `1.2.4.dev20251023154933`)
- Each build automatically gets a unique version number
- This allows testing multiple iterations without version conflicts

**For Testing:**
- Use `publish_test` task → TestPyPI for testing before production
- Or use the new `publish_pypi_force` task with `--skip-existing` flag

**For Production:**
- **Best practice:** Bump the version number with git tags (e.g., `git tag v1.2.4`)
- **Workaround:** Use the new `publish_pypi_force` task that includes `--skip-existing` flag (skips files that already exist)

**To delete a version:** You must have PyPI owner permissions and manually delete it from the PyPI web interface

### 3. Improved PyPI tasks with proper dependencies and caching

**DONE!** The pixi tasks now have:

✅ **Proper dependency chain** - Just run `pixi run publish_pypi` and it will:
1. Install build dependencies
2. Build wheel (cached if exists)
3. Repair wheel (cached if exists)
4. Build source distribution (cached if exists)
5. Check distributions with twine
6. Publish to PyPI

✅ **Smart caching** - Each build step checks if artifacts already exist:
- `build_wheel` - Skips if `.whl` file exists in `dist/`
- `repair_wheel` - Skips if `manylinux` wheel exists
- `build_sdist` - Skips if `.tar.gz` exists

✅ **Explicit rebuild** - Use `pixi run clean_dist` to force rebuilding everything

## New Workflow

### Development & Testing
```bash
# 1. Clean previous builds (only when you want to force rebuild)
pixi run clean_dist

# 2. Build everything with caching (fast if already built)
pixi run build_dist

# 3. Check distributions
pixi run check_dist

# 4. Test locally before publishing
pixi run install_local_wheel
pixi run test_installed_wheel

# 5. Publish to TestPyPI first
pixi run publish_test

# 6. If TestPyPI looks good, publish to PyPI
pixi run publish_pypi
```

### Simplified One-Command Workflow
```bash
# Just run this - it does everything with caching!
pixi run verify_publish_workflow

# Then review dist/ and publish
pixi run publish_pypi
```

### Force Publishing (skip existing versions)
```bash
pixi run publish_pypi_force
```

## Available Tasks

| Task | Description | Dependencies |
|------|-------------|--------------|
| `clean_dist` | Remove all build artifacts | None |
| `build_wheel` | Build GPU wheel (cached) | None |
| `repair_wheel` | Repair wheel for manylinux (cached) | `build_wheel` |
| `build_sdist` | Build source distribution (cached) | `install_build_deps` |
| `build_dist` | Build both wheel and sdist | `repair_wheel`, `build_sdist` |
| `check_dist` | Validate distributions with twine | `build_dist` |
| `install_local_wheel` | Install built wheel locally | `repair_wheel` |
| `test_installed_wheel` | Run full test suite on installed wheel | `install_local_wheel` |
| `publish_test` | Publish to TestPyPI (skips existing) | `check_dist` |
| `publish_pypi` | Publish to production PyPI | `check_dist` |
| `publish_pypi_force` | Publish to PyPI (skips existing) | `check_dist` |
| `verify_publish_workflow` | Complete verification workflow | `check_dist` |

## Caching Behavior

### When artifacts are cached (not rebuilt):
- **build_wheel**: If `dist/pymomentum_gpu-*-linux_x86_64.whl` and `dist/pymomentum_gpu-*-manylinux*.whl` exist
- **repair_wheel**: If `dist/pymomentum_gpu-*-manylinux*.whl` exists
- **build_sdist**: If `dist/*.tar.gz` exists

### To force rebuild:
```bash
pixi run clean_dist  # Removes all cached artifacts
```

### Typical workflow with caching:
```bash
# First time - builds everything
pixi run build_dist  # Takes several minutes

# Later - instant if no changes
pixi run build_dist  # Skips build, shows "✓ Wheel already exists..."

# After code changes - force rebuild
pixi run clean_dist
pixi run build_dist  # Rebuilds everything
```

## Version Management

Your project uses `setuptools-scm` for automatic versioning from git tags:

```bash
# Create a new version tag
git tag v1.2.3
git push --tags

# Build with new version
pixi run clean_dist
pixi run build_dist
```

Version scheme from `pyproject.toml`:
- **On tag**: `1.2.3`
- **Between tags**: `1.2.4.dev5+g1234abc`

The `local_scheme = "no-local-version"` ensures PyPI-compatible version strings.

## PyPI Credentials

Set up your PyPI credentials in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

Or use environment variables:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

## Troubleshooting

### "File already exists" error
- **Cause**: Trying to upload a version that already exists on PyPI
- **Solution**: Use `publish_pypi_force` or bump version with a new git tag

### Wheel is too large (>100MB)
- **Check**: You're excluding PyTorch/CUDA libraries in `repair_wheel`
- **Expected size**: ~56MB for GPU wheel
- **Verify**: `ls -lh dist/` should show reasonable sizes

### Import fails after install
- **Test locally first**: `pixi run install_local_wheel && pixi run test_installed_wheel`
- **Check dependencies**: Ensure torch is installed separately
- **Verify exclude list**: Make sure you're not excluding required libraries

### Caching issues
- **Force rebuild**: `pixi run clean_dist` before building
- **Check dist/**: Look for leftover artifacts from previous builds

## Best Practices

1. **Always test locally first**
   ```bash
   pixi run install_local_wheel
   pixi run test_installed_wheel
   ```

2. **Use TestPyPI for testing**
   ```bash
   pixi run publish_test
   # Test installation: pip install -i https://test.pypi.org/simple/ pymomentum-gpu
   ```

3. **Verify distributions before publishing**
   ```bash
   pixi run verify_publish_workflow
   twine check dist/*
   ```

4. **Bump version for each release**
   ```bash
   git tag v1.2.3
   git push --tags
   pixi run clean_dist
   pixi run publish_pypi
   ```

5. **Keep wheels small by excluding large dependencies**
   - PyTorch/LibTorch (users install separately)
   - CUDA libraries (users have their own)
   - MKL libraries (if not needed)

## Example: Full Release Process

```bash
# 1. Ensure you're on the right commit
git status
git log -1

# 2. Create and push version tag
git tag v1.0.0
git push origin v1.0.0

# 3. Clean and build
pixi run clean_dist
pixi run build_dist

# 4. Test locally
pixi run install_local_wheel
pixi run test_installed_wheel

# 5. Verify distributions
pixi run check_dist
ls -lh dist/

# 6. Test on TestPyPI first
pixi run publish_test

# 7. Test TestPyPI installation in a fresh environment
pip install -i https://test.pypi.org/simple/ pymomentum-gpu

# 8. If everything works, publish to production PyPI
pixi run publish_pypi

# 9. Verify installation from PyPI
pip install pymomentum-gpu
python -c "import pymomentum.geometry; print('Success!')"
```
