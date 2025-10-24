"""Content extractors for different sources"""

from typing import Protocol
from pathlib import Path
from .base import ContentExtractor
from .internal import InternalExtractor
from .external import ExternalExtractor


def get_extractor(mode: str) -> ContentExtractor:
    """Factory function to get appropriate extractor"""
    if mode == "internal":
        return InternalExtractor()
    elif mode == "external":
        return ExternalExtractor()
    else:
        raise ValueError(f"Unknown mode: {mode}")


__all__ = ["ContentExtractor", "get_extractor", "InternalExtractor", "ExternalExtractor"]
