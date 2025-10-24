#!/usr/bin/env python
# Copyright 2024 NetBox Labs Inc
"""Version stamp."""

# These properties are injected at build time by the build process.

__commit_hash__ = "cef0b2f"
__track__ = "release"
__version__ = "1.8.0"


def version_display():
    """Display the version, track and hash together."""
    return f"v{__version__}-{__track__}-{__commit_hash__}"


def version_semver():
    """Semantic version."""
    return __version__
