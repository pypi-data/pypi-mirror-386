from unittest.mock import patch

import pytest

from loopbot.client import AsyncOpenCodeClient
from loopbot.events import StepFinishEvent, StepStartEvent, TextEvent, ToolUseEvent
from loopbot.permissions import Permission


@pytest.mark.asyncio
@patch("loopbot.client.stream_opencode_cli")
async def test_client_stream_normalizes_and_skips(mock_stream_cli):
    """Client should normalize text payloads and skip empty markers."""

    raw_events = [
        # step_start without snapshot (allowed by schema)
        {
            "type": "step_start",
            "timestamp": 1,
            "sessionID": "ses_1",
            "part": {
                "id": "prt_1",
                "sessionID": "ses_1",
                "messageID": "msg_1",
                "type": "step-start",
            },
        },
        # text with top-level `text` key (normalized to `part`)
        {
            "type": "text",
            "timestamp": 2,
            "sessionID": "ses_1",
            "text": {
                "id": "prt_2",
                "sessionID": "ses_1",
                "messageID": "msg_1",
                "type": "text",
                "text": "hello",
                "time": {"start": 2, "end": 2},
            },
        },
        # malformed/empty text marker (should be skipped)
        {"type": "text", "timestamp": 3, "sessionID": "ses_1"},
        # tool_use event
        {
            "type": "tool_use",
            "timestamp": 4,
            "sessionID": "ses_1",
            "part": {
                "id": "prt_3",
                "sessionID": "ses_1",
                "messageID": "msg_1",
                "type": "tool",
                "callID": "call_1",
                "tool": "bash",
                "state": {
                    "status": "completed",
                    "input": {"command": "echo hi", "description": "say hi"},
                    "output": "hi\n",
                    "title": "echo hi",
                    "metadata": {"exit": 0},
                    "time": {"start": 4, "end": 4},
                },
            },
        },
        # step_finish without snapshot
        {
            "type": "step_finish",
            "timestamp": 5,
            "sessionID": "ses_1",
            "part": {
                "id": "prt_4",
                "sessionID": "ses_1",
                "messageID": "msg_1",
                "type": "step-finish",
                "cost": 0.0,
                "tokens": {
                    "input": 1,
                    "output": 1,
                    "reasoning": 0,
                    "cache": {"read": 0, "write": 0},
                },
            },
        },
    ]

    async def fake_stream():
        for ev in raw_events:
            yield ev

    mock_stream_cli.return_value = fake_stream()

    client = AsyncOpenCodeClient(model="m", permission=Permission())
    out = [event async for event in client.stream("prompt")]  # collect

    # Should skip the empty text marker, so 4 events remain
    assert len(out) == 4
    assert isinstance(out[0], StepStartEvent)
    assert isinstance(out[1], TextEvent)
    assert out[1].part.text == "hello"
    assert isinstance(out[2], ToolUseEvent)
    assert out[2].part.state.output.strip() == "hi"
    assert isinstance(out[3], StepFinishEvent)
