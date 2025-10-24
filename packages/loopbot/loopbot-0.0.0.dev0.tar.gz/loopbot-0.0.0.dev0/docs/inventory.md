### `docs` Inventory (Recommended)

This outlines a concise, task-focused docs plan for MkDocs. It mirrors the current SDK capabilities and provides quick paths for common workflows.

```
docs/
├── index.md                        # Landing page (adapted from README)
├── getting-started.md              # Install + 5‑minute quickstart
├── guides/
│   ├── 01-agents-and-sessions.md   # Stateless vs session flows; session IDs
│   ├── 02-permissions-and-tools.md # Permission model + bash/web/edit tool use
│   ├── 03-structured-outputs.md    # Pydantic models, fenced JSON parsing
│   ├── 04-async-usage.md           # AsyncAgent/AsyncSession usage patterns
│   ├── 05-working-directory.md     # Per-agent/session/call workdir (cwd)
│   ├── 06-error-handling.md        # LoopBotError, CliNotFoundError, CliExitError
│   ├── 07-testing-and-ci.md        # make check/test/coverage, uv matrix, E2E
│   └── 08-troubleshooting.md       # Common issues + fixes (env, paths, models)
└── api-reference.md                # mkdocstrings: `loopbot.*`
```

Notes and rationale
- Reuse README content for `index.md`, but keep it shorter and link to deeper guides.
- Add a dedicated Working Directory guide now that `workdir` is supported per agent/session/call.
- Merge permissions + tool use to show real bash/web examples alongside policy settings.
- Error handling deserves a page (what exceptions contain, how to surface stderr).
- Testing & CI should document:
  - `LOOPBOT_E2E=1` to enable real CLI tests
  - `make test-all-versions` (uv) and the GitHub Actions matrix
  - Why `_cli.py` is excluded from fast coverage and how E2E exercises it
- `api-reference.md` can be wired with mkdocstrings (e.g., `{% raw %}::: loopbot.agent.Agent{% endraw %}`) and grouped by module.

Navigation suggestion (mkdocs.yml)
```
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Guides:
      - Agents & Sessions: guides/01-agents-and-sessions.md
      - Permissions & Tools: guides/02-permissions-and-tools.md
      - Structured Outputs: guides/03-structured-outputs.md
      - Async Usage: guides/04-async-usage.md
      - Working Directory: guides/05-working-directory.md
      - Error Handling: guides/06-error-handling.md
      - Testing & CI: guides/07-testing-and-ci.md
      - Troubleshooting: guides/08-troubleshooting.md
  - API Reference: api-reference.md
```

Content pointers
- Prefer runnable snippets that mirror tests. For Working Directory, replicate the “two folders, two words” example.
- Keep prompts and outputs deterministic to avoid confusion in E2E flows.
- Link to `AGENTS.md` for contribution standards and Makefile targets.
