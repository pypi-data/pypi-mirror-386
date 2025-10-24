from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ._cli import stream_opencode_cli
from .events import (
    OpenCodeEvent,
    StepFinishEvent,
    StepStartEvent,
    TextEvent,
    ToolUseEvent,
)
from .permissions import Permission


def _normalize_raw_event(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize minor shape variations from different CLI versions.

    Observed variations:
    - Some streams emit text events with the `text` payload at top-level key
      `text` instead of under `part`. We map it to `part` for model parsing.
    """
    t = raw.get("type")
    if t == "text":
        # `{type: text, text: {...}}` → map to `part`
        if "part" not in raw and isinstance(raw.get("text"), dict):
            new_raw = dict(raw)
            new_raw["part"] = new_raw.pop("text")
            return new_raw
        # `{type: text}` with no payload → skip
        if "part" not in raw and "text" not in raw:
            return None
    return raw


def _parse_event(raw: dict[str, Any]) -> OpenCodeEvent:
    """Convert a raw dict into a typed event based on its `type` field.

    The CLI emits a top-level `type` of one of: `step_start`, `text`,
    `tool_use`, `step_finish`.
    """
    t = raw.get("type")
    if t == "step_start":
        return StepStartEvent.model_validate(raw)
    if t == "text":
        return TextEvent.model_validate(raw)
    if t == "tool_use":
        return ToolUseEvent.model_validate(raw)
    if t == "step_finish":
        return StepFinishEvent.model_validate(raw)
    # Unknown event types are considered a protocol error; surface clearly
    raise ValueError(f"Unknown event type: {t!r}")


class AsyncOpenCodeClient:
    """Async client that streams events from the OpenCode CLI."""

    def __init__(
        self,
        model: str,
        permission: Permission,
        providers: dict[str, Any] | None = None,
        workdir: str | None = None,
    ) -> None:
        self.model = model
        self.permission = permission
        self.providers = providers
        self.workdir = workdir

    async def stream(
        self, prompt: str, *, session_id: str | None = None, workdir: str | None = None
    ) -> AsyncIterator[OpenCodeEvent]:
        async for raw in stream_opencode_cli(
            prompt,
            model=self.model,
            permission=self.permission,
            providers=self.providers,
            session_id=session_id,
            cwd=workdir or self.workdir,
        ):
            normalized = _normalize_raw_event(raw)
            if normalized is None:
                continue
            yield _parse_event(normalized)
