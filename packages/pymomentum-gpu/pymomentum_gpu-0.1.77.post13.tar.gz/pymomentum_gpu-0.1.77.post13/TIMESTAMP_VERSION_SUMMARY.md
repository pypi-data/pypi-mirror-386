# Timestamp-Based Dev Version Summary

## Problem Solved

When publishing development versions (between git tags) to PyPI, you encountered version conflicts:
- PyPI doesn't allow overwriting the same version
- Dev versions like `1.2.4.dev5` would repeat across multiple builds
- This prevented iterative testing on PyPI

## Solution Implemented

Added custom version scheme that includes timestamps in dev versions.

###  Files Created/Modified

1. **`scm_version_scheme.py`** (NEW) - Custom version scheme for setuptools_scm
2. **`pyproject.toml`** - Updated to use custom version scheme
3. **`PYPI_PUBLISHING_GUIDE.md`** - Updated documentation

## How It Works

### Version Format

**Before:**
- Tagged release: `1.2.3`
- Dev (between tags): `1.2.4.dev5` (repeated on every build)

**After:**
- Tagged release: `1.2.3` (unchanged)
- Dev (between tags): `1.2.4.dev20251023141630` (unique timestamp)

### Technical Implementation

The custom version scheme in `scm_version_scheme.py`:

```python
def version_scheme_with_timestamp(version):
    # If it's a tagged release, use the tag version
    if version.exact:
        return version.format_with("{tag}")

    # For dev versions, include timestamp in format YYYYMMDDHHMMSS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    next_version = guess_next_version(version.tag)

    return f"{next_version}.dev{timestamp}"
```

### Configuration in pyproject.toml

```toml
[tool.setuptools_scm]
version_scheme = "scm_version_scheme:version_scheme_with_timestamp"
local_scheme = "no-local-version"
```

## Benefits

✅ **Unique versions** - Each build gets a unique version number
✅ **PyPI compatible** - No local version identifiers (no `+` suffixes)
✅ **Chronological** - Timestamps show build order
✅ **Testing friendly** - Can publish multiple test iterations
✅ **No manual intervention** - Fully automatic

## Usage Examples

### Publishing Dev Versions

```bash
# Build 1 (10:30 AM UTC)
pixi run build_dist
# Version: 1.2.4.dev20251023103000

# Fix a bug, build again (2:15 PM UTC)
pixi run clean_dist
pixi run build_dist
# Version: 1.2.4.dev20251023141500

# Both can be published to PyPI without conflicts!
pixi run publish_pypi
```

### Publishing Release Versions

```bash
# Tag a release
git tag v1.2.4
git push --tags

# Build and publish
pixi run clean_dist
pixi run build_dist
# Version: 1.2.4 (no timestamp, clean release)

pixi run publish_pypi
```

## Version Comparison

| Scenario | Old Version | New Version | PyPI Upload |
|----------|-------------|-------------|-------------|
| On tag v1.2.3 | 1.2.3 | 1.2.3 | ✅ Unique |
| Dev build #1 | 1.2.4.dev5 | 1.2.4.dev20251023103000 | ✅ Unique |
| Dev build #2 | 1.2.4.dev5 | 1.2.4.dev20251023141500 | ✅ Unique |
| After 1 commit | 1.2.4.dev6 | 1.2.4.dev20251023150000 | ✅ Unique |

## Testing the Version Scheme

To verify what version will be generated:

```bash
# Check current version
pixi run -e gpu python -c "from setuptools_scm import get_version; print(get_version())"

# Build and check embedded version
pixi run build_dist
unzip -p dist/pymomentum_gpu-*.whl pymomentum_gpu-*.dist-info/METADATA | grep Version
```

## Notes

- **UTC timestamps** - Uses UTC to ensure consistency across timezones
- **14-digit format** - `YYYYMMDDHHMMSS` provides second-level granularity
- **PEP 440 compliant** - Format follows Python packaging standards
- **Automatic** - No manual version management needed for dev builds

## When NOT to Use

This timestamp versioning is **only for dev versions** (commits between tags). For releases:

1. **Create a git tag**: `git tag v1.2.4`
2. **Push the tag**: `git push --tags`
3. **Build with clean version**: The version will be `1.2.4` (no timestamp)

## Troubleshooting

### Timestamps not appearing

**Symptom:** Version still shows `1.2.4.dev5` without timestamp

**Causes:**
1. Custom version scheme not being loaded
2. Cached version from previous build
3. Module import error (silently swallowed)

**Solutions:**
```bash
# 1. Clean everything
pixi run clean_dist
rm -f pymomentum/_version.py

# 2. Verify the module loads
pixi run -e gpu python -c "import scm_version_scheme; print(scm_version_scheme)"

# 3. Rebuild
pixi run build_dist

# 4. Check version in built wheel
unzip -p dist/pymomentum_gpu-*.whl */METADATA | grep "^Version:"
```

### Version shows "+g..." suffix

**Symptom:** Version like `1.2.4.dev20251023103000+g1234abc`

**Cause:** `local_scheme` not set to `no-local-version`

**Solution:** Verify `pyproject.toml` has:
```toml
[tool.setuptools_scm]
local_scheme = "no-local-version"
```

## Integration with Existing Workflow

The timestamp versioning integrates seamlessly with your existing pixi tasks:

```bash
# No changes needed to your workflow!
pixi run clean_dist      # Clean old builds
pixi run build_dist      # Build with timestamp version
pixi run check_dist      # Verify distributions
pixi run publish_pypi    # Publish to PyPI
```

## Related Documentation

- `PYPI_PUBLISHING_GUIDE.md` - Complete publishing workflow
- `PYTORCH_COMPATIBILITY.md` - PyTorch version compatibility
- `PYTORCH_VERSION_FIX.md` - PyTorch ABI fix details

## Summary

You can now publish unlimited dev iterations to PyPI without version conflicts. Each build gets a unique timestamp-based version that's:
- ✅ Automatically generated
- ✅ PyPI compatible
- ✅ Chronologically ordered
- ✅ PEP 440 compliant

Just build and publish - the versioning handles itself!
