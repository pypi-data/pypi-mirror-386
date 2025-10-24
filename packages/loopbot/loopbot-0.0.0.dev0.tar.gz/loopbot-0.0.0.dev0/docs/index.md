# LoopBot

LoopBot is a Python SDK for invoking the OpenCode CLI programmatically. It provides a small, layered API that streams JSON events from the CLI and aggregates them into friendly Python objects.

- Sync and async usage (`Agent`, `AsyncAgent`)
- Sessions with automatic session ID capture
- Pydantic structured outputs (validated with Pydantic models)
- Permissions for tools (bash/web/edit)
- Configurable working directory per agent, session, or call

```python
from loopbot import Agent, Permission

agent = Agent(
    model="anthropic/claude-haiku-4-5",
    permission=Permission(bash=Permission.DENY),
)

with agent.session() as s:
    s.invoke("Remember: magic")
    r = s.invoke("What is the word?")
    print(r.output)
```

See Getting Started for a 5‑minute setup, or dive into the Guides for specific workflows.

Key guides:
- [Structured Outputs](guides/03-structured-outputs.md)
- [Async Usage](guides/04-async-usage.md)
