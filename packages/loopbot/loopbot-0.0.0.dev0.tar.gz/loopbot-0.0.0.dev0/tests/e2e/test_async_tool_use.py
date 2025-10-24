import os

import pytest

from loopbot import AsyncAgent, Permission, Response
from loopbot.events import ToolUseEvent

MODEL = os.environ.get("LOOPBOT_MODEL", "anthropic/claude-haiku-4-5")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_async_session_tool_use_ls() -> None:
    """
    Validates that the async session can perform a bash tool use (ls) and
    return the output, while preserving session state.
    """
    if not os.environ.get("LOOPBOT_E2E"):
        pytest.skip("Set LOOPBOT_E2E=1 to run end-to-end tests.")

    permission = Permission(
        edit=Permission.DENY,
        bash=Permission.ALLOW,  # enable tool use
        webfetch=Permission.DENY,
    )

    agent = AsyncAgent(model=MODEL, permission=permission)

    async with agent.session() as session:
        # Ask the agent to explicitly use bash to list E2E tests
        prompt = (
            "Use the bash tool to run: ls -1 tests/e2e\n"
            "Return only the raw command output."
        )
        response: Response[str] = await session.invoke(prompt)
        assert isinstance(response, Response)
        assert response.session_id

        # Must see a bash tool_use event in the stream
        assert any(
            isinstance(e, ToolUseEvent) and e.part.tool == "bash"
            for e in response.events
        ), "Expected a bash tool_use event in the response stream"

        # Should include known test files in output
        # We match on filenames that exist in repo
        # Output may be reported as a text chunk or only in the tool state
        tool_out = "\n".join(
            e.part.state.output for e in response.events if isinstance(e, ToolUseEvent)
        )
        combined = (response.raw_text or "") + "\n" + tool_out
        assert "test_session.py" in combined or "test_structured.py" in combined
