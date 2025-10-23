"""
MaruAdmin Agent - Remote server management agent
"""
from pathlib import Path

# Read version from VERSION file
_version_file = Path(__file__).parent / "VERSION"
__version__ = _version_file.read_text().strip()
__author__ = "MaruAdmin Team"