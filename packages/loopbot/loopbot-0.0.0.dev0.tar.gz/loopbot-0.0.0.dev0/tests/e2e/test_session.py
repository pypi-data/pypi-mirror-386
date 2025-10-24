import os

import pytest

from loopbot import Agent, Permission, Response

# --- Configuration ---
# Allow overriding the model via environment variable for flexibility in testing
MODEL = os.environ.get("LOOPBOT_MODEL", "anthropic/claude-haiku-4-5")


@pytest.mark.e2e
def test_sync_session_remembers_context():
    """
    Validates that the sync Agent, using a session context manager, can
    maintain context between two separate invocations.
    """
    # Skip this test unless explicitly enabled, as it makes real API calls.
    if not os.environ.get("LOOPBOT_E2E"):
        pytest.skip("Set LOOPBOT_E2E=1 to run end-to-end tests.")

    # 1. Configure the Agent with a restrictive permission set
    permission = Permission(
        edit=Permission.DENY,
        bash=Permission.DENY,
        webfetch=Permission.DENY,
    )

    agent = Agent(model=MODEL, permission=permission)

    with agent.session() as session:
        # Request
        response1 = session.invoke("Remember the word: magic")
        assert isinstance(response1, Response)
        assert isinstance(response1.output, str)
        assert response1.session_id is not None, "Session ID should be captured"
        assert len(response1.events) > 0, "Should have received events"

        # Recall
        response2 = session.invoke("What is the word?")
        assert isinstance(response2, Response)
        assert isinstance(response2.output, str)
        # This is the most critical check:
        assert "magic" in response2.output.lower(), "Agent failed to recall the word"
        assert response2.session_id == response1.session_id, (
            "Session ID must be consistent"
        )
