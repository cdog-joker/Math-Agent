"""Load prompt templates with repository-relative paths."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = PROJECT_ROOT / "prompts"


def load_prompt(filename: str) -> str:
    path = PROMPT_DIR / filename
    return path.read_text(encoding="utf-8").strip()
