"""
pa_assistant
============

Core library for the Personal Activity Tracking Assistant (Phase 1 MVP).

This package provides:
- Data models for normalized activity entries.
- Connectors for Google Drive and local LLM logs (Gemini, Perplexity).
- Markdown report generation utilities.
- A small runner/CLI entrypoint for local testing.
"""

from .models import ActivityEntry, Platform

__all__ = ["ActivityEntry", "Platform"]

