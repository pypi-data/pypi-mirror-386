from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .events import OpenCodeEvent, ToolUseEvent
from .usage import UsageMetrics

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """High-level response object returned by the Agent.

    - `output`: final value (raw text by default or structured by a parser)
    - `session_id`: session identifier used for this exchange
    - `events`: full stream of typed events from the CLI
    - `raw_text`: concatenation of all text event chunks
    - `usage`: token/cost accounting rolled up from step-finish events
    """

    output: str | T
    session_id: str
    events: list[OpenCodeEvent] = Field(default_factory=list)
    raw_text: str = ""
    usage: UsageMetrics = Field(default_factory=UsageMetrics)

    @property
    def tool_events(self) -> list[ToolUseEvent]:
        return [e for e in self.events if isinstance(e, ToolUseEvent)]
