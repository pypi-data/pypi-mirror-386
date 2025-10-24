"""Core pantsonfire application"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import json
import time

from .config import Config
from .llm import LLMClient
from .extractors import ContentExtractor, get_extractor
from .storage import StorageBackend, JSONStorage
from .models import CheckResult, TruthSource


class PantsonfireApp:
    """Main pantsonfire application"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = LLMClient(config) if not config.dry_run else None

        # Initialize storage backend
        if config.storage_backend == "oxen":
            from .storage.oxen_storage import OxenStorage
            self.storage = OxenStorage(config)
        else:
            from .storage.json_storage import JSONStorage
            self.storage = JSONStorage(config.storage_path)

        self.extractor = get_extractor(config.mode)

    def check_content(
        self,
        blog_source: Union[str, Path],
        truth_sources: List[Union[str, Path]],
        output_format: str = "json",
        blog_content: Optional[str] = None
    ) -> List[CheckResult]:
        """
        Check blog content against truth sources for misinformation.

        Args:
            blog_source: URL/path to blog post
            truth_sources: List of URLs/paths to truth/reference documents
            output_format: Output format ('json', 'text', 'csv')
            blog_content: Pre-extracted blog content (optional, for crawled content)

        Returns:
            List of detected issues
        """
        # Use provided content or extract it
        if blog_content is None:
            blog_content = self._extract_with_fallback(blog_source)
            if not blog_content:
                raise ValueError(f"Could not extract content from {blog_source}")

        # Extract truth content
        truth_content = []
        for source in truth_sources:
            content = self._extract_with_fallback(source)
            if content:
                truth_content.append(TruthSource(source=str(source), content=content))

        if not truth_content:
            raise ValueError("Could not extract any truth source content")

        # Perform cross-referencing
        results = self._cross_reference(blog_content, truth_content)

        # Ensure results is a list
        if results is None:
            results = []

        # Store results
        # Initialize Oxen analysis if needed
        if hasattr(self.storage, 'initialize_analysis') and getattr(self.storage, 'current_repo', None) is None:
            analysis_name = f"check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = self.storage.initialize_analysis(analysis_name)
            if not success:
                print("⚠️  Warning: Failed to initialize Oxen analysis, falling back to local storage")

        try:
            self.storage.save_results(results)
        except Exception as storage_error:
            print(f"⚠️  Storage failed: {storage_error}, but continuing with results")

        return results

    def _extract_with_fallback(self, source: Union[str, Path]) -> Optional[str]:
        """
        Extract content using traditional methods first, then browser automation for modern sites.

        Args:
            source: URL or file path to extract from

        Returns:
            Extracted content, or None if all methods fail
        """
        # Try traditional extraction first
        content = self.extractor.extract(source)

        # If traditional extraction succeeded and has substantial content, use it
        if content and len(content.strip()) > 100:
            return content

        # For web URLs, if traditional extraction returned minimal content,
        # the browser automation fallback is already handled in the ExternalExtractor
        # So we just return what we got

        return content  # Return whatever we got, even if minimal

    def _is_web_url(self, source: Union[str, Path]) -> bool:
        """Check if source is a web URL (not a file path)"""
        source_str = str(source)
        return source_str.startswith(('http://', 'https://'))

    def _cross_reference(
        self,
        blog_content: str,
        truth_sources: List[TruthSource]
    ) -> List[CheckResult]:
        """Cross-reference blog content against truth sources"""
        results = []

        # Split blog content into chunks
        blog_chunks = self._chunk_text(blog_content, self.config.max_chunk_size)

        for i, chunk in enumerate(blog_chunks):
            # Check each chunk against all truth sources
            for truth_source in truth_sources:
                truth_chunks = self._chunk_text(truth_source.content, self.config.max_chunk_size)

                for j, truth_chunk in enumerate(truth_chunks):
                    # Use LLM to compare chunks
                    comparison = self.llm.compare_content(
                        blog_chunk=chunk,
                        truth_chunk=truth_chunk,
                        context=f"Blog chunk {i+1}, Truth source: {truth_source.source}"
                    )

                    if comparison and comparison.confidence >= self.config.confidence_threshold:
                        result = CheckResult(
                            blog_source="unknown",  # Will be set by caller
                            truth_source=truth_source.source,
                            discrepancy=comparison.discrepancy,
                            confidence=comparison.confidence,
                            evidence=comparison.evidence,
                            chunk_index=i,
                            timestamp=datetime.now()
                        )
                        results.append(result)

                    # Rate limiting
                    time.sleep(self.config.rate_limit_delay)

        return results

    def _chunk_text(self, text: str, max_size: int) -> List[str]:
        """Split text into chunks of maximum size"""
        if len(text) <= max_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = ""

        for word in words:
            if len(current_chunk + " " + word) <= max_size:
                current_chunk += " " + word if current_chunk else word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_logs(self, limit: Optional[int] = None) -> List[CheckResult]:
        """Retrieve stored detection logs"""
        return self.storage.get_results(limit)

    def export_logs(self, output_path: Path, format: str = "json") -> None:
        """Export logs to file"""
        results = self.get_logs()
        self.storage.export_results(results, output_path, format)
