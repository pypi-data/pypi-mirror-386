"""Data models for pantsonfire"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class TruthSource(BaseModel):
    """A source of truth for verification"""
    source: str
    content: str


class ComparisonResult(BaseModel):
    """Result of comparing blog content against truth"""
    discrepancy: str
    confidence: float
    evidence: str
    reasoning: Optional[str] = None


class CheckResult(BaseModel):
    """Result of a content check"""
    blog_source: str
    truth_source: str
    discrepancy: str
    confidence: float
    evidence: str
    chunk_index: int
    timestamp: datetime
    tags: Optional[List[str]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "blog_source": self.blog_source,
            "truth_source": self.truth_source,
            "discrepancy": self.discrepancy,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "chunk_index": self.chunk_index,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags or []
        }


class ContentChunk(BaseModel):
    """A chunk of extracted content"""
    content: str
    source: str
    chunk_type: str = "text"  # 'text', 'code', 'heading', etc.
