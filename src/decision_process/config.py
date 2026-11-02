"""API keys for the decision process, loaded from the .env file.

The .env file sits at the project root and is ignored by git, so keys never
reach GitHub. See .env.example for the names it should contain.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# This file is src/decision_process/config.py, so the root is two folders up
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

# Empty values in .env ("KEY=") are treated as missing
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY") or None
NCBI_API_KEY: str | None = os.getenv("NCBI_API_KEY") or None  # optional


def require_gemini_api_key() -> str:
    """The Gemini API key, or a clear error if it is missing from .env."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            f"GEMINI_API_KEY is not set. Add it to {PROJECT_ROOT / '.env'}"
        )
    return GEMINI_API_KEY
