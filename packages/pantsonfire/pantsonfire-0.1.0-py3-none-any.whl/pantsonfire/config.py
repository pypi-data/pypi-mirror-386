"""Configuration management for pantsonfire"""

from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for pantsonfire application"""

    mode: str = Field(default="external", description="Operation mode: 'internal' or 'external'")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter base URL")
    model: str = Field(default="anthropic/claude-3-haiku", description="LLM model to use")

    # Storage configuration
    storage_backend: str = Field(default="oxen", description="Storage backend: 'json' or 'oxen'")
    storage_path: Path = Field(default=Path("./pantsonfire_logs.json"), description="Path for storing detection logs (JSON backend)")

    # Oxen AI configuration
    oxen_base_url: str = Field(default="https://hub.oxen.ai", description="Oxen Hub base URL")
    oxen_namespace: str = Field(default="pantsonfire", description="Oxen namespace for repositories")
    oxen_api_key: Optional[str] = Field(default=None, description="Oxen API key for authentication")

    # Web scraping configuration
    crawl_enabled: bool = Field(default=False, description="Enable web crawling for broader analysis")
    crawl_depth: int = Field(default=1, description="Depth for web crawling")
    crawl_max_pages: int = Field(default=10, description="Maximum pages to crawl")

    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold for flagging issues")
    max_chunk_size: int = Field(default=2000, description="Maximum chunk size for text processing")
    rate_limit_delay: float = Field(default=1.0, description="Delay between API calls to avoid rate limits")
    dry_run: bool = Field(default=False, description="Run in dry-run mode without LLM analysis")

    def is_internal_mode(self) -> bool:
        """Check if running in internal mode"""
        return self.mode == "internal"

    def is_external_mode(self) -> bool:
        """Check if running in external mode"""
        return self.mode == "external"
