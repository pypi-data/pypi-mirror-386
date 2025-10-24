import os

import pytest

from loopbot import AsyncAgent, Permission, Response

MODEL = os.environ.get("LOOPBOT_MODEL", "anthropic/claude-haiku-4-5")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_async_session_remembers_context() -> None:
    """
    Validates that the AsyncAgent, using an AsyncSession, can maintain context
    between two separate invocations.
    """
    # Skip unless explicitly enabled, as it makes real CLI calls.
    if not os.environ.get("LOOPBOT_E2E"):
        pytest.skip("Set LOOPBOT_E2E=1 to run end-to-end tests.")

    permission = Permission(
        edit=Permission.DENY,
        bash=Permission.DENY,
        webfetch=Permission.DENY,
    )

    agent = AsyncAgent(model=MODEL, permission=permission)
    session = agent.session()

    # Request
    response1 = await session.invoke("Remember the word: magic")
    assert isinstance(response1, Response)
    assert isinstance(response1.output, str)
    assert response1.session_id, "Session ID should be captured"
    assert response1.events, "Should have received events"

    # Recall
    response2 = await session.invoke("What is the word?")
    assert isinstance(response2, Response)
    assert isinstance(response2.output, str)
    assert "magic" in response2.output.lower(), "Agent failed to recall the word"
    assert response2.session_id == response1.session_id, "Session ID must be consistent"
