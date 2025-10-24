"""JSON-based storage for pantsonfire results"""

import json
import csv
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from ..models import CheckResult
from .base import StorageBackend


class JSONStorage(StorageBackend):
    """Store results in JSON format"""

    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_results(self, results: List[CheckResult]) -> None:
        """Save check results to JSON file"""
        # Load existing results
        existing_results = self._load_results()

        # Convert new results to dicts and add them
        new_results = [result.to_dict() for result in results]
        all_results = existing_results + new_results

        # Save back to file
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

    def get_results(self, limit: Optional[int] = None) -> List[CheckResult]:
        """Retrieve stored results"""
        raw_results = self._load_results()

        if limit:
            raw_results = raw_results[-limit:]  # Get most recent

        results = []
        for raw in raw_results:
            try:
                # Convert back to CheckResult
                result = CheckResult(
                    blog_source=raw["blog_source"],
                    truth_source=raw["truth_source"],
                    discrepancy=raw["discrepancy"],
                    confidence=raw["confidence"],
                    evidence=raw["evidence"],
                    chunk_index=raw["chunk_index"],
                    timestamp=datetime.fromisoformat(raw["timestamp"]),
                    tags=raw.get("tags", [])
                )
                results.append(result)
            except Exception as e:
                print(f"Failed to parse stored result: {e}")

        return results

    def export_results(
        self,
        results: List[CheckResult],
        output_path: Path,
        format: str = "json"
    ) -> None:
        """Export results to file in specified format"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            self._export_json(results, output_path)
        elif format.lower() == "csv":
            self._export_csv(results, output_path)
        elif format.lower() in ["txt", "text"]:
            self._export_text(results, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _load_results(self) -> List[dict]:
        """Load results from storage file"""
        if not self.storage_path.exists():
            return []

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load results from {self.storage_path}: {e}")
            return []

    def _export_json(self, results: List[CheckResult], output_path: Path) -> None:
        """Export as JSON"""
        data = [result.to_dict() for result in results]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, results: List[CheckResult], output_path: Path) -> None:
        """Export as CSV"""
        if not results:
            return

        fieldnames = [
            'blog_source', 'truth_source', 'discrepancy', 'confidence',
            'evidence', 'chunk_index', 'timestamp', 'tags'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = result.to_dict()
                row['tags'] = ';'.join(row['tags']) if row['tags'] else ''
                writer.writerow(row)

    def _export_text(self, results: List[CheckResult], output_path: Path) -> None:
        """Export as human-readable text"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Pantsonfire Detection Results\n")
            f.write("=" * 50 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"ISSUE #{i}\n")
                f.write(f"Blog Source: {result.blog_source}\n")
                f.write(f"Truth Source: {result.truth_source}\n")
                f.write(f"Confidence: {result.confidence:.2f}\n")
                f.write(f"Discrepancy: {result.discrepancy}\n")
                f.write(f"Evidence: {result.evidence}\n")
                f.write(f"Timestamp: {result.timestamp}\n")
                if result.tags:
                    f.write(f"Tags: {', '.join(result.tags)}\n")
                f.write("\n" + "-" * 30 + "\n\n")
