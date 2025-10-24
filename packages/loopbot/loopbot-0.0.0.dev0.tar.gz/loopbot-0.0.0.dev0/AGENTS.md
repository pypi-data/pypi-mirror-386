# Repository Guidelines

This guide helps contributors work efficiently in this repository.

## Project Structure & Module Organization
- `src/loopbot/` — Python SDK
  - `agent.py` (Agent, AsyncAgent, sessions)
  - `client.py` (event parsing + normalization)
  - `events.py` (typed event models)
  - `_cli.py` (CLI wrapper subprocess)
  - `permissions.py` (Permission + levels)
  - `response.py`, `usage.py`, `structured.py`
- `tests/` — pytest suite
  - `unit/` focuses on models and parsing
  - `e2e/` runs real CLI flows (guarded by env)
- `Makefile` — dev shortcuts; see below

## Build, Test, and Development Commands
- `make dev-install` — install dev deps
- `make check` — format (Black), lint (Ruff), type-check (ty/mypy)
- `make test` — run unit (E2E skipped by default)
- `LOOPBOT_E2E=1 make test` — enable real CLI tests
- `make coverage` — coverage report (fast; excludes `_cli.py`)
- `make clean` — remove build and cache artifacts
- `make test-all-versions` — run tests on multiple Python versions via uv
  - CI runs this matrix on 3.10–3.14 (E2E off by default)

## Coding Style & Naming Conventions
- Python ≥ 3.10, type hints required (mypy strict baseline)
- Formatting: Black (79 chars); Lint: Ruff; Import order enforced
- Names: snake_case for functions/vars, PascalCase for classes
- Errors: raise precise exceptions (see `errors.py`); no bare `except`
- Asynchrony: prefer async-first implementations; provide sync wrappers as thin adapters
- Working directory: pass per-agent/session/call (`workdir`) instead of changing process CWD

## Testing Guidelines
- Framework: pytest; markers: `@pytest.mark.e2e` for real CLI tests
- E2E are opt-in via `LOOPBOT_E2E=1`; keep deterministic prompts
- Unit tests live in `tests/unit/` and validate parsing/contracts
- Test files: `tests/**/test_*.py`; prefer behavior tests over implementation details

## Commit & Pull Request Guidelines
- Commits: concise, imperative mood (e.g., "Add async session E2E")
- PRs must include: purpose, summary of changes, and testing instructions
- Requirements before review:
  - `make check` passes (no lint/type errors)
  - `make test` passes; run E2E locally when your changes affect `_cli.py`
  - Update docs/examples if behavior or API changes

## Security & Configuration Tips
- E2E uses the real `opencode` binary; avoid secrets in prompts
- Permissions default to safe settings; tighten in tests with `Permission.DENY`
- The CLI is configured via `OPENCODE_CONFIG_CONTENT` (set by the SDK)

## Quick Usage
```python
from loopbot import Agent, Permission
agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
with agent.session() as s:
    print(s.invoke("Hello").output)
```
