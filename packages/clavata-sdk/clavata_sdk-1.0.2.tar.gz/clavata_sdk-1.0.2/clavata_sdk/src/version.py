"""SDK version metadata."""

import importlib.metadata

try:
    # When installed as a package, read version from package metadata
    __version__ = importlib.metadata.version("clavata-sdk")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development (when not installed as a package)
    __version__ = "dev"


def get_client_header_value() -> str:
    """Returns the x-clavata-client header value in format: python-sdk:VERSION"""
    return f"python-sdk:{__version__}"
