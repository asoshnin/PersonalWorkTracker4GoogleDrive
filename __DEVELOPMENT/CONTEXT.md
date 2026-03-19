# Project Context

## What this project is

A Python CLI tool that fetches Google Drive activity and generates a Markdown report
to help users recall what they were working on. Entry point: pa_assistant/cli.py

## Current state

- Auth: Service Account (needs migration to OAuth 2.0 User Flow)
- Data source: Drive API v3 files.list() (needs migration to Drive Activity API v2)
- Output: Flat Markdown table (needs sessionization and structured report format)
- Tests: None currently exist

## Refactoring document

Full instructions are in: __DEVELOPMENT/2026-03-19_12-47_refactoring.md

## Key files

- pa_assistant/cli.py — entry point, CLI args
- pa_assistant/runner.py — orchestration, loads config (DO NOT MODIFY unless instructed)
- pa_assistant/connectors/drive.py — Google Drive integration (primary target for Phase 0)
- pa_assistant/connectors/llm_logs.py — log reader (has hardcoded paths to fix)
- pa_assistant/models.py — ActivityEntry data model
- pa_assistant/report.py — report generator (target for Phase 1)
- pa_config.yaml — single source of truth for configuration
