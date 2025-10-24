# LoopBot

Python SDK for invoking the [OpenCode](https://opencode.ai/) coding agent CLI in a headless, non-interactive manner.

Supports:

- Synchronous and Asynchronous modes
- Structured outputs using Pydantic models
- Sessions for multiple invocations with shared context
- Permission configuration for reading, writing, web, and bash tools
- Configurable working directory per agent, session, or call


## Installation

You can install `loopbot` using `uv` (recommended) or `pip`.

```bash
# Using uv
uv pip install loopbot

# Using pip
pip install loopbot
```

## Usage

Here are a few ways to use the `loopbot` SDK, from simple invocations to stateful, asynchronous sessions.

### 1. Basic Synchronous Agent

This is the simplest way to get a response from an agent. Permissions are configured to prevent the agent from performing any actions on your system.

```python
from loopbot import Agent, Permission

# Configure a restrictive agent that cannot execute bash commands
agent = Agent(
    model="anthropic/claude-sonnet-4-5",
    permission=Permission(
        webfetch=Permission.ALLOW,
    )
)

# Invoke the agent with a prompt
response = agent.invoke("Do web search for 'opencode.ai zen models' and list them")

print(response.output)
```

```markdown
## OpenCode Zen Models

- **GPT 5** (`gpt-5`)
- **GPT 5 Codex** (`gpt-5-codex`)
- **Claude Sonnet 4.5** (`claude-sonnet-4-5`)
- **Claude Sonnet 4** (`claude-sonnet-4`)
- **Claude Haiku 4.5** (`claude-haiku-4-5`)
- **Claude Haiku 3.5** (`claude-3-5-haiku`)
- **Claude Opus 4.1** (`claude-opus-4-1`)
- **Qwen3 Coder 480B** (`qwen3-coder`)
- **Grok Code Fast 1** (`grok-code`) - Currently free
- **Kimi K2** (`kimi-k2`)
- **Code Supernova** - Currently free (stealth model)
```

### 2. Structured Outputs with Pydantic

Get clean, validated data back from the agent by providing a Pydantic model. The agent will automatically format its response to fit the schema.

```python
from loopbot import Agent, Permission
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    name: str = Field(description="The user's full name.")
    age: int = Field(description="The user's age in years.")

# Allow the agent to use web search but not file system or bash access
agent = Agent(
    model="anthropic/claude-haiku-4-5",
    permission=Permission(
        bash=Permission.DENY,
        edit=Permission.DENY,
        webfetch=Permission.ALLOW,
    )
)

# The agent will return a populated UserProfile instance
response = agent.invoke_structured(
    "Extract the user's information: My name is Jane Doe and I am 28 years old.",
    model_cls=UserProfile
)

user = response.output
print(f"Name: {user.name}, Age: {user.age}")
# > Name: Jane Doe, Age: 28
```

### 3. Stateful Sessions

Use a session to have a conversation where the agent remembers previous interactions. The session manager automatically handles passing the session ID between calls.

```python
from loopbot import Agent, Permission

agent = Agent(
    model="anthropic/claude-haiku-4-5",
    permission=Permission(bash=Permission.DENY)
)

with agent.session() as s:
    # First turn: The agent remembers the word "avocado"
    s.invoke("Please remember this word for me: avocado")

    # Second turn: The agent recalls the word from the session context
    response = s.invoke("What was the word I asked you to remember?")
    print(response.output)
    # > The word you asked me to remember was "avocado".
```

### 4. Asynchronous Usage

For non-blocking applications, `loopbot` provides an async-native `AsyncAgent` and `AsyncSession`.

```python
import asyncio
from loopbot import AsyncAgent, Permission

async def main():
    agent = AsyncAgent(
        model="anthropic/claude-haiku-4-5",
        permission=Permission(bash=Permission.DENY)
    )

    async with agent.session() as s:
        await s.invoke("Remember this number: 42")
        response = await s.invoke("What was the number?")
        print(response.output)

asyncio.run(main())
```

### 5. Working Directory (CWD)

The `opencode` subprocess runs in a chosen CWD. You can set it:

- Per agent (default): `Agent(..., workdir="/path/to/project")`
- Per session: `agent.session(workdir="/path/to/project")`
- Per call: `agent.invoke("...", workdir="/path/to/project")`

Example with session-scoped CWD:

```python
from loopbot import Agent, Permission

agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.ALLOW))
with agent.session(workdir="/tmp/projectA") as s:
    r = s.invoke("Use the bash tool to run: ls -1")
    print(r.output)
```

## How It Works

`loopbot` is a lightweight wrapper that orchestrates calls to the `opencode` command-line tool. Understanding its mechanism can help you use it more effectively.

*   **Headless CLI Invocation**: The SDK executes `opencode run` as a subprocess in a non-interactive, JSON-streaming mode. It does not require the TUI.
*   **Dynamic Configuration**: Agent settings, such as the model and permissions, are passed to the CLI on-the-fly using the `OPENCODE_CONFIG_CONTENT` environment variable. This avoids the need for on-disk `opencode.json` files.
*   **Event Streaming**: The CLI streams a series of JSON objects representing events (`step_start`, `text`, `tool_use`, `step_finish`). The SDK parses these events into typed Python objects.
*   **Working Directory**: The `opencode` subprocess runs in a configured CWD (per agent/session/call). If unspecified, it inherits the current process CWD.
*   **Session Management**: Session IDs are extracted from the event stream and automatically passed back to the CLI in subsequent calls using the `--session` flag.

For more information on the underlying agent, check out the official [OpenCode Documentation](https://opencode.ai/docs/).

## Testing & CI

- Local: `make check` (format, lint, type-check), `make test` (unit tests; E2E skipped), `make coverage`.
- Multi-version: `make test-all-versions` (uses uv; override with `PY_VERSIONS="3.12 3.13"`).
- CI: GitHub Actions runs tests on Python 3.10–3.14 using uv (E2E remains opt-in).
