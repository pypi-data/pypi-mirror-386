# PyPI Publishing Guide for pymomentum-gpu

> **Note:** This repository now publishes only the `pymomentum-gpu` package (GPU-accelerated version with CUDA support). For detailed GPU-specific publishing instructions, see [PUBLISHING_GPU.md](PUBLISHING_GPU.md).

This guide provides general information about publishing Python packages to PyPI. For GPU-specific workflows and requirements, refer to the dedicated GPU publishing guide.

## Overview

The publishing setup consists of three main components:

1. **`pyproject.toml`** - Contains package metadata and build configuration
2. **`pixi.toml`** - Includes local development and publishing tasks
3. **`.github/workflows/publish_to_pypi.yml`** - Automated GitHub Actions workflow for CI/CD

## Automated Publishing via GitHub Actions

### Prerequisites

Before you can publish automatically, you need to set up PyPI Trusted Publishing:

1. **Create a PyPI account** at https://pypi.org (or https://test.pypi.org for testing)

2. **Set up Trusted Publishing on PyPI:**
   - Go to your project on PyPI (create it if it doesn't exist)
   - Navigate to "Publishing" settings
   - Add a new "Trusted Publisher"
   - Configure:
     - **Owner:** `facebookresearch`
     - **Repository:** `momentum`
     - **Workflow:** `publish_to_pypi.yml`
     - **Environment:** `pypi`

3. **Configure GitHub environment:**
   - In your GitHub repository, go to Settings → Environments
   - Create an environment named `pypi`
   - (Optional) Add protection rules like requiring reviewers

### Publishing a New Release

To publish a new version to PyPI:

1. **Update the version number** in `pyproject.toml`:
   ```toml
   [project]
   name = "pymomentum"
   version = "0.2.0"  # Update this
   ```

2. **Create and push a version tag:**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. **Monitor the workflow:**
   - Go to Actions tab in GitHub
   - Watch the "Publish to PyPI" workflow
   - It will:
     - Build wheels for Linux, macOS (Intel & ARM), and Windows
     - Build wheels for Python 3.10, 3.11, and 3.12
     - Create a source distribution
     - Publish to PyPI

### Testing Before Release

To test the publishing workflow before an actual release:

1. **Manually trigger the workflow:**
   - Go to Actions → "Publish to PyPI"
   - Click "Run workflow"
   - Check "Publish to TestPyPI instead of PyPI"
   - Click "Run workflow"

2. **Test the published package:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ pymomentum
   ```

## Local Testing and Publishing

For manual publishing or testing, you can use the pixi tasks.

**Note:** The Python `build` package is not available in conda-forge, so you need to install it via pip:

```bash
pip install build
```

This package is required for the `build_wheel`, `build_sdist`, and `build_dist` tasks.

### Clean Distribution Artifacts

Remove old build artifacts before creating new distributions:

```bash
pixi run clean_dist
```

### Build Distribution Files Locally

```bash
# Build wheel only
pixi run build_wheel

# Build source distribution only
pixi run build_sdist

# Build both wheel and sdist
pixi run build_dist
```

### Check Distribution Files

Before publishing, verify your distributions:

```bash
pixi run check_dist
```

This will check for common issues like:
- Missing required metadata
- Invalid file formats
- Rendering issues in README

### Test Local Installation

Test that the built wheel works correctly:

```bash
# Install the locally built wheel
pixi run install_local_wheel

# Verify import and version
pixi run test_local_install
```

### Full Local Verification Workflow

Run the complete verification workflow in one command:

```bash
pixi run verify_publish_workflow
```

This will:
1. Clean old artifacts
2. Build distributions
3. Check distributions
4. List the created files

### Publish to TestPyPI

Test your package on TestPyPI first:

```bash
pixi run publish_test
```

You'll need a TestPyPI account and API token. Configure it in `~/.pypirc`:

```ini
[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

### Publish to PyPI

Once tested, publish to production PyPI:

```bash
pixi run publish_pypi
```

You'll need a PyPI account and API token. Configure it in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE
```

## Workflow Details

### Build Matrix

The GitHub Actions workflow builds wheels for:

- **Operating Systems:**
  - Ubuntu (latest)
  - macOS 13 (Intel)
  - macOS 14 (ARM)
  - Windows (latest)

- **Python Versions:**
  - 3.10
  - 3.11
  - 3.12

### Build Configuration

The build uses `scikit-build-core` with these CMake arguments:

- `BUILD_SHARED_LIBS=OFF` - Static linking for portability
- `MOMENTUM_BUILD_PYMOMENTUM=ON` - Build Python bindings
- `MOMENTUM_BUILD_EXAMPLES=OFF` - Skip examples in wheel
- `MOMENTUM_BUILD_TESTING=OFF` - Skip tests in wheel
- `MOMENTUM_ENABLE_SIMD=ON` - Enable SIMD optimizations
- `MOMENTUM_USE_SYSTEM_GOOGLETEST=OFF` - Bundle dependencies
- `MOMENTUM_USE_SYSTEM_PYBIND11=OFF` - Bundle pybind11

## Package Metadata

The package metadata in `pyproject.toml` includes:

- **Name:** `pymomentum`
- **Description:** Foundational algorithms for human kinematic motion
- **License:** MIT
- **Python Support:** >= 3.10
- **URLs:** Documentation, repository, bug reports

### Keywords

The package is tagged with relevant keywords for discoverability:
- kinematics
- motion
- optimization
- human-motion
- inverse-kinematics
- forward-kinematics
- body-tracking
- motion-capture
- character-animation
- robotics

## Troubleshooting

### Build Failures

If builds fail in GitHub Actions:

1. Check the Actions logs for specific error messages
2. Test the build locally using `pixi run build_dist`
3. Ensure all dependencies are properly specified
4. Verify CMake configuration is correct

### Publishing Failures

If publishing fails:

1. **Trusted Publishing not configured:**
   - Verify PyPI Trusted Publishing settings
   - Check GitHub environment configuration

2. **Version already exists:**
   - PyPI doesn't allow re-uploading the same version
   - Increment version number in `pyproject.toml`

3. **Authentication errors:**
   - For local publishing, check your `~/.pypirc` configuration
   - Ensure API tokens are valid

### Platform-Specific Issues

**Linux:** Requires system dependencies (boost, eigen, etc.)
**macOS:** May need Xcode command line tools
**Windows:** Requires Visual Studio 2022 or later

## Best Practices

1. **Always test on TestPyPI first** before publishing to production
2. **Use semantic versioning** (e.g., 0.1.0, 0.2.0, 1.0.0)
3. **Update CHANGELOG** before each release
4. **Tag releases** in git with version numbers
5. **Test wheels** on different platforms after building
6. **Document breaking changes** in release notes
7. **Run `verify_publish_workflow`** before publishing

## Example Publishing Workflow

Here's a complete example of the recommended publishing workflow:

```bash
# 1. Update version in pyproject.toml
# Edit: version = "0.2.0"

# 2. Run local verification
pixi run verify_publish_workflow

# 3. Test on TestPyPI
pixi run publish_test

# 4. Install from TestPyPI and test
pip install --index-url https://test.pypi.org/simple/ pymomentum

# 5. If everything works, commit and tag
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin main
git push origin v0.2.0

# 6. The GitHub Actions workflow will automatically publish to PyPI
```

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [scikit-build-core Documentation](https://scikit-build-core.readthedocs.io/)
- [Twine Documentation](https://twine.readthedocs.io/)
