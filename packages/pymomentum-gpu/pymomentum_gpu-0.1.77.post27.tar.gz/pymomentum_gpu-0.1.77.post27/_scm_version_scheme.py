# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.
"""
Custom version scheme for setuptools_scm that includes timestamps in dev versions.

This allows publishing multiple dev versions to PyPI without version conflicts.
Dev versions will be formatted as: 1.2.3.devYYYYMMDDHHMMSS

Example versions:
  - On tag v1.2.3: 1.2.3
  - Dev version: 1.2.4.dev20251023135047
"""

from datetime import datetime, timezone


def version_scheme_with_timestamp(version):
    """
    Custom version scheme that adds timestamp to dev versions.

    Args:
        version: Version object from setuptools_scm

    Returns:
        String version number
    """
    # If it's a tagged release, use the tag version
    if version.exact:
        return version.format_with("{tag}")

    # For dev versions, include timestamp
    # Generate timestamp in format YYYYMMDDHHMMSS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # Get base version (tag without 'v' prefix)
    tag_version = str(version.tag).lstrip("v")

    # Parse the version to increment the patch number
    parts = tag_version.split(".")
    if len(parts) >= 3:
        # Increment patch version
        major, minor, patch = parts[0], parts[1], parts[2]
        next_patch = int(patch) + 1
        next_version = f"{major}.{minor}.{next_patch}"
    else:
        # Fallback if version format is unexpected
        next_version = tag_version

    # Format as: next_version.devTIMESTAMP
    return f"{next_version}.dev{timestamp}"
