"""Answer extraction and normalization helpers."""

from __future__ import annotations

import re


FINAL_PATTERNS = [
    re.compile(r"(?:FINAL_ANSWER|Final Answer|final answer)\s*[:：]\s*(.+)", re.I | re.S),
    re.compile(r"(?:最终答案|答案)\s*[:：]\s*(.+)", re.S),
    re.compile(r"\\boxed\{(.+?)\}", re.S),
]


def extract_final_answer(text: str) -> str:
    if not text:
        return ""

    for pattern in FINAL_PATTERNS:
        match = pattern.search(text)
        if match:
            return normalize_final_answer(match.group(1))

    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return ""

    # Prefer the last short line, because LLMs often end with the answer alone.
    for line in reversed(lines):
        cleaned = normalize_final_answer(line)
        if cleaned and len(cleaned) <= 120:
            return cleaned

    return normalize_final_answer(lines[-1])


def normalize_final_answer(answer: str) -> str:
    if answer is None:
        return ""

    text = str(answer).strip()
    text = _strip_markdown_fence(text)
    text = text.strip()
    text = re.sub(r"^(?:FINAL_ANSWER|Final Answer|final answer|最终答案|答案)\s*[:：]\s*", "", text)
    text = text.strip()

    if text.startswith("$") and text.endswith("$") and len(text) >= 2:
        text = text[1:-1].strip()

    text = _unwrap_boxed(text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.rstrip("。.;；")
    return text.strip()


def _strip_markdown_fence(text: str) -> str:
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1])
    return text


def _unwrap_boxed(text: str) -> str:
    match = re.fullmatch(r"\\boxed\{(.+)\}", text, flags=re.S)
    if match:
        return match.group(1).strip()
    return text
