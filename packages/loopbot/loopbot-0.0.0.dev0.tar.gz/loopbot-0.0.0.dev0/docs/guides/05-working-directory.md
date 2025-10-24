# Working Directory (CWD)

Run the CLI in a specific folder. Choose at any level:

- Per agent: `Agent(..., workdir="/path")`
- Per session: `agent.session(workdir="/path")`
- Per call: `agent.invoke("...", workdir="/path")`

Example
```python
from loopbot import Agent, Permission
agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.ALLOW))
with agent.session(workdir="/tmp/projectA") as s:
    r = s.invoke("Use the bash tool to run: ls -1")
    print(r.output)
```

Tips
- Prefer session-level defaults for multi-step tasks.
- Avoid `os.chdir()` in apps that host multiple agents.

Best practices
- Prefer the `workdir` parameter over `os.chdir()`. It scopes the working directory to the subprocess only, avoiding global CWD changes that can interfere with concurrent agents or other parts of your application.
