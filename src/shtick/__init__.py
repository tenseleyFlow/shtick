"""
shtick - Shell alias manager
"""

__version__ = "1.0.0"

# Export the high-level API for easy importing
from .shtick import ShtickManager

# Make it available at package level
__all__ = ["ShtickManager"]
