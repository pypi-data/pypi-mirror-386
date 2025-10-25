"""Application factory for pantsonfire"""

from typing import Optional, Dict, Any
from pathlib import Path
import os
from .core import PantsonfireApp
from .config import Config


def create_app(mode: str = "internal", config: Optional[Dict[str, Any]] = None) -> PantsonfireApp:
    """
    Create a pantsonfire application instance.

    Args:
        mode: 'internal' for local/offline mode, 'external' for web-based mode
        config: Optional configuration overrides

    Returns:
        Configured PantsonfireApp instance
    """
    if config is None:
        config = {}

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Default configuration
    default_config = {
        "mode": mode,
        "storage_backend": "oxen",  # Use Oxen by default
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "oxen_api_key": os.getenv("OXEN_API_KEY"),
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "model": "anthropic/claude-3-haiku",  # Default to cheaper model, can be overridden
        "storage_path": Path("./pantsonfire_logs.json"),
        "confidence_threshold": 0.7,
        "max_chunk_size": 2000,
        "rate_limit_delay": 1.0,
    }

    # Merge with provided config
    final_config = {**default_config, **config}

    app_config = Config(**final_config)

    return PantsonfireApp(app_config)
