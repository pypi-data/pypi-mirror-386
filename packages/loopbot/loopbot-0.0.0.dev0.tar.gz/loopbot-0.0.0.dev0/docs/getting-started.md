# Getting Started

This page gets you from zero to a working call in minutes.

## Install

```bash
uv pip install loopbot
# or
pip install loopbot
```

## Minimal example

```python
from loopbot import Agent, Permission

agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
resp = agent.invoke("Say hello in one short sentence.")
print(resp.output)
```

## Next steps
- Sessions for context: see "Agents & Sessions"
- Pydantic structured outputs: see "Structured Outputs"
- Working directory control: see "Working Directory"
- Async usage: see "Async Usage"

## Requirements
> Note: LoopBot wraps the external `opencode` CLI. Make sure the `opencode` binary is installed and available on your system `PATH` before running examples. The SDK shells out to `opencode run --format json` and streams events.
