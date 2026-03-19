## Language & Runtime

- Python 3.10+
- All code must pass `python -m pytest` without errors

## Code Style

- Follow PEP8 strictly
- All functions must have docstrings
- Use type hints on all function signatures
- Use pathlib.Path for all file path operations, never raw strings

## Architecture Rules

- NEVER modify runner.py without explicit instruction — it is the orchestration core
- NEVER hardcode paths, credentials, or date values — all must come from pa_config.yaml
- token.json must ALWAYS be in .gitignore — verify this before completing any auth task
- New connectors must follow the same interface pattern as the existing drive.py connector

## Testing

- Write at minimum one unit test for every new function using pytest + unittest.mock
- Mock all Google API calls — never make real API calls in tests

## Scope Control

- Before starting any task, list the exact files you intend to modify
- If the task requires touching more than 5 files, produce a plan Artifact first and wait for approval
- Do not refactor code outside the defined task scope, even if you see improvements
