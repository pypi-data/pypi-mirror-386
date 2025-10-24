"""MCP Package Hero - Get latest package versions from PyPI, npm, and pub.dev."""

from .models import Ecosystem, PackageVersion, VersionStatus
from .server import mcp

__version__ = "1.0.0"
__all__ = ["Ecosystem", "PackageVersion", "VersionStatus", "mcp"]
