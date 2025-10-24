# Structured Outputs

Get validated data by supplying a Pydantic model.

```python
from pydantic import BaseModel
from loopbot import Agent, Permission

class User(BaseModel):
    name: str
    age: int

agent = Agent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
r = agent.invoke_structured("My name is Alice and I am 30.", model_cls=User)
print(r.output)
```

Notes
- The SDK decorates prompts with your model’s JSON schema and instructs the agent to respond with a fenced JSON block. LoopBot then extracts and validates that JSON against the Pydantic model.
- If the output does not conform to the schema, a `ValueError` is raised with details to help you debug.
