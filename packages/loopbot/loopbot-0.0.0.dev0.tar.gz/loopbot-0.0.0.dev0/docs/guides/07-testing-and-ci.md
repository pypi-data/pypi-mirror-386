# Testing & CI

## Local
- `make check` — format (Black), lint (Ruff), type-check (ty)
- `make test` — unit tests; E2E skipped
- `make coverage` — fast coverage (excludes CLI wrapper)

Enable E2E (real CLI):
```bash
LOOPBOT_E2E=1 make test
```

## Multiple Python versions
Run tests across versions using uv:
```bash
make test-all-versions
# or
PY_VERSIONS="3.12 3.13" make test-all-versions ARGS="-q"
```

## CI
GitHub Actions runs a matrix on 3.10–3.14 via uv (E2E opt-in). See `.github/workflows/ci.yml`.

Coverage omission
- The `_cli.py` module shells out to external binaries and is excluded from fast unit coverage runs. Its behavior is exercised by the E2E suite, which invokes the real `opencode` binary.
