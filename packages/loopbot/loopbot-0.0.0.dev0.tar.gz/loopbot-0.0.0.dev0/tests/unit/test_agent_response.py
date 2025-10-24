import pytest

from loopbot.agent import AsyncAgent
from loopbot.events import StepFinishEvent, TextEvent
from loopbot.permissions import Permission


def _text_event(text: str, ts: int = 1) -> TextEvent:
    raw = {
        "type": "text",
        "timestamp": ts,
        "sessionID": "ses_u",
        "part": {
            "id": f"prt_t{ts}",
            "sessionID": "ses_u",
            "messageID": "msg_1",
            "type": "text",
            "text": text,
            "time": {"start": ts, "end": ts},
        },
    }
    return TextEvent.model_validate(raw)


def _finish_event(cost: float, inp: int, out: int, ts: int = 99) -> StepFinishEvent:
    raw = {
        "type": "step_finish",
        "timestamp": ts,
        "sessionID": "ses_u",
        "part": {
            "id": f"prt_f{ts}",
            "sessionID": "ses_u",
            "messageID": "msg_1",
            "type": "step-finish",
            "cost": cost,
            "tokens": {
                "input": inp,
                "output": out,
                "reasoning": 0,
                "cache": {"read": 0, "write": 0},
            },
        },
    }
    return StepFinishEvent.model_validate(raw)


@pytest.mark.asyncio
async def test_agent_aggregates_response_and_usage():
    events = [
        _text_event("Hello ", 1),
        _text_event("World", 2),
        _finish_event(0.2, 10, 5),
    ]

    class FakeClient:
        async def stream(
            self,
            prompt: str,
            *,
            session_id: str | None = None,
            workdir: str | None = None,
        ):
            for e in events:
                yield e

    agent = AsyncAgent(model="m", permission=Permission())
    # Inject fake client
    agent._client = FakeClient()

    resp = await agent.invoke("ignored")

    assert resp.output == "Hello World"
    assert resp.raw_text == "Hello World"
    assert resp.session_id == "ses_u"
    assert resp.usage.total_cost == 0.2
    assert resp.usage.input_tokens == 10
    assert resp.usage.output_tokens == 5
    assert len(resp.events) == 3


@pytest.mark.asyncio
async def test_agent_parser_transforms_output():
    events = [_text_event("abc", 1)]

    class FakeClient:
        async def stream(
            self,
            prompt: str,
            *,
            session_id: str | None = None,
            workdir: str | None = None,
        ):
            for e in events:
                yield e

    agent = AsyncAgent(model="m", permission=Permission())
    agent._client = FakeClient()

    resp = await agent.invoke("ignored", parser=lambda s: s.upper())
    assert resp.output == "ABC"
    assert resp.raw_text == "abc"
