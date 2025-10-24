"""
Version management for Salt Docs.
Centralized version definition for consistency.
"""

# Current version - update this when releasing
__version__ = "0.1.2"


def get_version():
    """
    Get the current version.

    Returns:
        str: The current version string (e.g., "0.1.2")
    """
    return __version__
