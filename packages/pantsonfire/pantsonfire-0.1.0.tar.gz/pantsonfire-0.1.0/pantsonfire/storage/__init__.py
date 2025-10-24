"""Storage backends for pantsonfire results"""

from .base import StorageBackend
from .json_storage import JSONStorage

__all__ = ["StorageBackend", "JSONStorage"]
