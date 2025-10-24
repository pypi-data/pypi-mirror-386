from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from loopbot.client import _parse_event
from loopbot.events import (
    BaseEvent,
    StepFinishEvent,
    StepStartEvent,
    TextEvent,
    ToolUseEvent,
)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "blocks.jsonl"


def _load_rows() -> list[dict]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


@pytest.mark.parametrize(
    "index, expected_cls",
    [
        (0, StepStartEvent),
        (1, ToolUseEvent),
        (2, TextEvent),
        (3, ToolUseEvent),
        (4, StepFinishEvent),
        (5, StepStartEvent),
        (6, TextEvent),
        (7, StepFinishEvent),
    ],
)
def test_event_rows_parse_into_models(
    index: int, expected_cls: type[BaseEvent]
) -> None:
    rows = _load_rows()
    row = rows[index]
    model_cls = {
        "step_start": StepStartEvent,
        "tool_use": ToolUseEvent,
        "text": TextEvent,
        "step_finish": StepFinishEvent,
    }[row["type"]]

    event = model_cls.model_validate(row)
    assert isinstance(event, expected_cls)
    assert event.sessionID == "ses_5f2db5107ffebYvhHPqkEvRtRP"


def test_event_field_values_from_fixture() -> None:
    rows = _load_rows()
    events = [
        StepStartEvent.model_validate(rows[0]),
        ToolUseEvent.model_validate(rows[1]),
        TextEvent.model_validate(rows[2]),
        ToolUseEvent.model_validate(rows[3]),
        StepFinishEvent.model_validate(rows[4]),
        StepStartEvent.model_validate(rows[5]),
        TextEvent.model_validate(rows[6]),
        StepFinishEvent.model_validate(rows[7]),
    ]

    step_start_1, tool_1, text_1, tool_2, finish_1, step_start_2, text_2, finish_2 = (
        events
    )

    assert step_start_1.part.type == "step-start"
    assert step_start_1.part.snapshot == "1d3734ba72e6d2ce2baf7d10b1ede3d457c98b9d"

    assert tool_1.part.tool == "bash"
    assert tool_1.part.state.input.command == "python session_chat.py"
    assert tool_1.part.state.metadata["exit"] == 0
    assert tool_1.part.state.time.start == 1761157101670

    assert text_1.part.text.strip().startswith("I'll run both Python files")
    assert text_1.part.time.start == text_1.part.time.end == 1761157102041

    assert tool_2.part.state.input.command == "python simple_chat.py"
    assert tool_2.part.state.output.endswith("SDK not yet implemented\n")

    assert finish_1.part.tokens.cache.read == 13069
    assert finish_1.part.tokens.input == 13070

    assert step_start_2.part.id == "prt_a0d24bc87001dV8Y6SPZa0IRP9"
    assert step_start_2.part.snapshot == "1d3734ba72e6d2ce2baf7d10b1ede3d457c98b9d"

    assert text_2.part.text.endswith('SDK not yet implemented"')
    assert text_2.part.time.start == 1761157102911

    assert finish_2.part.cost == 0
    assert finish_2.part.tokens.output == 21
    assert finish_2.part.tokens.cache.read == 13166


def test_invalid_text_block_shape_is_reported() -> None:
    """The final JSONL row omits `part` and should fail validation."""

    malformed_row = _load_rows()[8]
    assert malformed_row["type"] == "text"
    assert "part" not in malformed_row

    with pytest.raises(ValidationError):
        TextEvent.model_validate(malformed_row)


def test_unknown_event_type_is_reported() -> None:
    """Unknown top-level event types should raise a clear ValueError."""
    raw = {"type": "banana", "timestamp": 0, "sessionID": "ses_test"}
    with pytest.raises(ValueError) as exc:
        _parse_event(raw)
    assert "Unknown event type" in str(exc.value)
