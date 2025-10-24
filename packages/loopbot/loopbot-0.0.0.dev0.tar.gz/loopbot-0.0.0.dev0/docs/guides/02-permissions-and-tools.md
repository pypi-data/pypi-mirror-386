# Permissions & Tools

Control what the agent can do using `Permission`.

```python
from loopbot import Agent, Permission
p = Permission(
  bash=Permission.ASK,   # ask before running bash
  edit=Permission.DENY,  # no file writes
  webfetch=Permission.ALLOW,
)
agent = Agent(model="anthropic/claude-haiku-4-5", permission=p)
```

Example: request a bash command
```python
r = agent.invoke("Use the bash tool to run: ls -1")
print(r.raw_text)
# See also: r.tool_events for ToolUseEvent objects
```

Recommendations
- Default to `DENY` in tests; allow only what’s needed.
- When verifying tool output, prefer `ToolUseEvent.part.state.output` for reliability.

Inspecting tool usage
```python
response = agent.invoke("Use the bash tool to run: ls -1")
for event in response.tool_events:
    if event.part.tool == "bash":
        print(event.part.state.output)
```
