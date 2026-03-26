"""
helpers.py – Utility functions for DRCode.

Provides:
  • Structured logging configuration
  • Environment variable loading with defaults
  • Temporary file management
"""

import os
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────────
#  Load .env at import time
# ──────────────────────────────────────────────
load_dotenv()


def get_env(key: str, default: str = "") -> str:
    """Retrieve an environment variable with an optional default."""
    return os.getenv(key, default)


# ──────────────────────────────────────────────
#  Logging
# ──────────────────────────────────────────────
def setup_logging(name: str = "drcode", level: int = logging.INFO) -> logging.Logger:
    """
    Create and return a consistently-formatted logger.

    Args:
        name:  Logger namespace (default ``drcode``).
        level: Logging level (default ``INFO``).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


# ──────────────────────────────────────────────
#  Temporary file helpers
# ──────────────────────────────────────────────
TEMP_DIR = Path(tempfile.gettempdir()) / "drcode_uploads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def save_temp_file(content: bytes, filename: str) -> Path:
    """
    Persist raw bytes to a temporary file and return its path.

    Args:
        content:  Raw file bytes.
        filename: Original filename (used for extension detection).

    Returns:
        :class:`Path` to the saved temporary file.
    """
    filepath = TEMP_DIR / filename
    filepath.write_bytes(content)
    return filepath


def cleanup_temp_file(filepath: Path) -> None:
    """Silently remove a temporary file if it exists."""
    try:
        if filepath.exists():
            filepath.unlink()
    except OSError:
        pass
