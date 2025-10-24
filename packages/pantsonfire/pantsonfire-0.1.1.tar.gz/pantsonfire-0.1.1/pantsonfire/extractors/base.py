"""Base content extractor interface"""

from typing import Protocol, Union, Optional
from pathlib import Path


class ContentExtractor(Protocol):
    """Protocol for content extraction from various sources"""

    def extract(self, source: Union[str, Path]) -> Optional[str]:
        """
        Extract readable content from a source.

        Args:
            source: URL string or file path

        Returns:
            Extracted text content, or None if extraction failed
        """
        ...

    def can_handle(self, source: Union[str, Path]) -> bool:
        """
        Check if this extractor can handle the given source.

        Args:
            source: URL string or file path

        Returns:
            True if this extractor can handle the source
        """
        ...
