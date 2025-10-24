import os

import pytest
from pydantic import BaseModel, Field

from loopbot import Agent, Permission, Response

MODEL = os.environ.get("LOOPBOT_MODEL", "anthropic/claude-haiku-4-5")


class UserProfile(BaseModel):
    name: str = Field(description="The user's full name.")
    age: int = Field(description="The user's age in years.")


@pytest.mark.e2e
def test_sync_structured_output() -> None:
    """
    Validates that the agent can return a structured Pydantic model in the
    Response object. This test makes a real CLI call and is skipped unless
    LOOPBOT_E2E=1.
    """
    if not os.environ.get("LOOPBOT_E2E"):
        pytest.skip("Set LOOPBOT_E2E=1 to run end-to-end tests.")

    agent = Agent(model=MODEL, permission=Permission(bash=Permission.DENY))

    prompt = (
        "Extract the user's information: My name is John Doe and I am 30 years old."
    )

    response: Response[UserProfile] = agent.invoke_structured(
        prompt, model_cls=UserProfile
    )

    assert isinstance(response, Response)
    assert isinstance(response.output, UserProfile), (
        "The 'output' field should be a UserProfile instance"
    )
    assert response.output.name.lower() == "john doe"
    assert response.output.age == 30

    assert "john doe" in response.raw_text.lower()
    assert len(response.events) > 0
    assert response.usage.total_cost >= 0
