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

from setuptools_scm.version import guess_next_version  # type: ignore[import-not-found]


def version_scheme_with_timestamp(version):
    """
    Custom version scheme that adds timestamp to dev versions.

    Args:
        version: Version object from setuptools_scm

    Returns:
        String version number with format: MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH.devTIMESTAMP
    """
    # If it's a tagged release, return just the tag (stripped of 'v' prefix)
    if version.exact:
        return version.format_with("{tag}")

    # For dev versions, include timestamp
    # Generate timestamp in format YYYYMMDDHHMMSS
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # Get the next version using setuptools_scm's helper
    next_version = guess_next_version(version.tag)

    # Format as: next_version.devTIMESTAMP
    return f"{next_version}.dev{timestamp}"
