# Error Handling

Errors are explicit and typed:

- `LoopBotError`: base class
- `CliNotFoundError`: `opencode` executable not found
- `CliExitError`: CLI exited non-zero (includes `return_code` and `stderr`)

Example
```python
from loopbot.errors import CliNotFoundError, CliExitError
from loopbot import Agent, Permission

try:
    agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission())
    agent.invoke("Hello")
except CliNotFoundError:
    print("Install 'opencode' and ensure it is on PATH")
except CliExitError as e:
    print(e.return_code, e.stderr)
```

Details
- `CliExitError.return_code`: the process exit status (e.g., 127).
- `CliExitError.stderr`: captured stderr from the CLI, useful for logs and debugging.
