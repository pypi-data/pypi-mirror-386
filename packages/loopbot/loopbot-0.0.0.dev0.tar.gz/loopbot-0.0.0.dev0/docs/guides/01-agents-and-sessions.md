# Agents & Sessions

LoopBot offers a simple API for one-off calls and stateful conversations.

## One-off
```python
from loopbot import Agent, Permission
agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
print(agent.invoke("Say hi in 3 words").output)
```

## Sessions
```python
from loopbot import Agent, Permission
agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
with agent.session() as s:
    s.invoke("Remember: magic")
    print(s.invoke("What is the word?").output)
```

Tips
- Sessions automatically capture the first session ID and reuse it.
- Use sessions when the second prompt depends on earlier context.

How it maintains context
- The first response includes a `sessionID` in the event stream. The `Session` helper captures that value and automatically supplies it on subsequent calls, so the CLI treats them as a single ongoing conversation.

When to use a session
- Use a session when you need the model to remember prior turns (e.g., “remember X”, then “what was X?”), or when you want to keep tool outputs and decisions within the same conversational context.
