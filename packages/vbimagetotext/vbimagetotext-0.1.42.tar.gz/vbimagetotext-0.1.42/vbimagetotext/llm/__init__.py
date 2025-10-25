"""Lightweight wrappers around OpenAI Responses API for features.

Each module focuses on a single responsibility (classify, solve, etc.).
These avoid reusing legacy code paths and do not perform OCR.
"""

__all__ = [
    "classify",
    "solve",
    "utils",
]

