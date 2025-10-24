"""Base storage backend interface"""

from typing import Protocol, List, Optional
from pathlib import Path
from ..models import CheckResult


class StorageBackend(Protocol):
    """Protocol for storing and retrieving pantsonfire results"""

    def save_results(self, results: List[CheckResult]) -> None:
        """Save check results"""
        ...

    def get_results(self, limit: Optional[int] = None) -> List[CheckResult]:
        """Retrieve stored results"""
        ...

    def export_results(
        self,
        results: List[CheckResult],
        output_path: Path,
        format: str = "json"
    ) -> None:
        """Export results to file"""
        ...
