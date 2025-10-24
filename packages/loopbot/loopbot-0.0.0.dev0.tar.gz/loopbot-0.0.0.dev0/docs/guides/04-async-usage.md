# Async Usage

Async-first APIs provide non-blocking flows.

```python
import asyncio
from loopbot import AsyncAgent, Permission

async def main():
    agent = AsyncAgent(model="anthropic/claude-haiku-4-5", permission=Permission(bash=Permission.DENY))
    async with agent.session() as s:
        await s.invoke("Remember: 42")
        r = await s.invoke("What was the number?")
        print(r.output)

asyncio.run(main())
```

API symmetry
- `AsyncAgent` and `AsyncSession` mirror the synchronous APIs (`Agent`, `Session`), so switching between blocking and non‑blocking code paths generally means adding `await` and using the async constructors.
