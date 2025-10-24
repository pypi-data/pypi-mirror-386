import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from .client import AsyncOpenCodeClient
from .events import OpenCodeEvent, StepFinishEvent, TextEvent
from .permissions import Permission
from .response import Response
from .structured import build_structured_prompt, create_structured_parser

T = TypeVar("T")
P = TypeVar("P", bound=BaseModel)


class AsyncAgent:
    """The core asynchronous agent for interacting with the OpenCode CLI.

    This class wraps an async client that streams JSON events from the CLI and
    aggregates them into a `Response`. Sessions are supported by capturing the
    first observed session ID and reusing it for subsequent calls.
    """

    def __init__(
        self,
        model: str,
        permission: Permission,
        providers: dict[str, Any] | None = None,
        workdir: str | None = None,
    ) -> None:
        self._client = AsyncOpenCodeClient(
            model, permission, providers, workdir=workdir
        )
        self._session_id: str | None = None

    async def invoke(
        self,
        prompt: str,
        *,
        session_id: str | None = None,
        parser: Callable[[str], T] | None = None,
        workdir: str | None = None,
    ) -> Response[T]:
        """Invoke the agent and return an aggregated `Response`.

        - `prompt`: natural language instruction for the agent
        - `session_id`: override the active session (typically omitted)
        - `parser`: optional callable to transform the final text into a
          structured object (future structured outputs can integrate here)
        """
        events: list[OpenCodeEvent] = []
        text_chunks: list[str] = []

        response_session_id = session_id or self._session_id

        async for event in self._client.stream(
            prompt, session_id=response_session_id, workdir=workdir
        ):
            events.append(event)

            # Capture session id from first event if not explicitly provided
            if response_session_id is None:
                response_session_id = event.sessionID

            if isinstance(event, TextEvent):
                text_chunks.append(event.part.text)

        # Aggregate results
        raw_text = "".join(text_chunks)

        # Optional parser for structured outputs (middleware can hook here later)
        output: Any
        if parser is not None:
            output = parser(raw_text)
        else:
            output = raw_text

        resp: Response[Any] = Response(
            output=output,
            raw_text=raw_text,
            session_id=response_session_id or "",  # set after first event
            events=events,
        )

        # Roll-up usage from step-finish events
        for ev in events:
            if isinstance(ev, StepFinishEvent):
                resp.usage.total_cost += ev.part.cost
                resp.usage.input_tokens += ev.part.tokens.input
                resp.usage.output_tokens += ev.part.tokens.output
                resp.usage.reasoning_tokens += ev.part.tokens.reasoning

        # Persist session across calls when using the agent directly
        if self._session_id is None and resp.session_id:
            self._session_id = resp.session_id

        return resp  # type: ignore[return-value]

    def session(self, workdir: str | None = None) -> "AsyncSession":
        return AsyncSession(self, workdir=workdir)

    async def invoke_structured(
        self,
        prompt: str,
        *,
        model_cls: type[P],
        session_id: str | None = None,
        workdir: str | None = None,
    ) -> Response[P]:
        """Invoke the agent requesting a structured Pydantic model output."""
        structured_prompt = build_structured_prompt(prompt, model_cls)
        parser = create_structured_parser(model_cls)
        return await self.invoke(
            structured_prompt, session_id=session_id, parser=parser, workdir=workdir
        )


class Agent:
    """Synchronous wrapper around `AsyncAgent`.

    Provides an easy-to-use interface for most Python applications.
    """

    def __init__(
        self,
        model: str,
        permission: Permission,
        providers: dict[str, Any] | None = None,
        workdir: str | None = None,
    ) -> None:
        self._async_agent = AsyncAgent(model, permission, providers, workdir=workdir)

    def invoke(
        self,
        prompt: str,
        *,
        session_id: str | None = None,
        parser: Callable[[str], T] | None = None,
        workdir: str | None = None,
    ) -> Response[T]:
        return asyncio.run(
            self._async_agent.invoke(
                prompt, session_id=session_id, parser=parser, workdir=workdir
            )
        )

    def session(self, workdir: str | None = None) -> "Session":
        return Session(self, workdir=workdir)

    def invoke_structured(
        self,
        prompt: str,
        *,
        model_cls: type[P],
        session_id: str | None = None,
        workdir: str | None = None,
    ) -> Response[P]:
        """Synchronous helper returning a `Response` with typed Pydantic output."""
        return asyncio.run(
            self._async_agent.invoke_structured(
                prompt, model_cls=model_cls, session_id=session_id, workdir=workdir
            )
        )


class AsyncSession:
    """Asynchronous session manager for stateful conversations."""

    def __init__(self, agent: AsyncAgent, workdir: str | None = None) -> None:
        self._agent = agent
        self.session_id: str | None = None
        self.workdir: str | None = workdir

    async def __aenter__(self) -> "AsyncSession":  # pragma: no cover (E2E exercised)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # pragma: no cover
        # Nothing to clean up; context manager exists for ergonomic symmetry.
        return None

    async def invoke(
        self,
        prompt: str,
        *,
        parser: Callable[[str], T] | None = None,
        workdir: str | None = None,
    ) -> Response[T]:
        effective_cwd = workdir if workdir is not None else self.workdir
        response = await self._agent.invoke(
            prompt, session_id=self.session_id, parser=parser, workdir=effective_cwd
        )
        if self.session_id is None:
            self.session_id = response.session_id
        return response


class Session:
    """Synchronous session manager for stateful conversations.

    Usage:
        agent = Agent(...)
        with agent.session() as s:
            s.invoke("...1...")
            s.invoke("...2...")  # shares the same session id
    """

    def __init__(self, agent: Agent, workdir: str | None = None) -> None:
        self._agent = agent
        self.session_id: str | None = None
        self.workdir: str | None = workdir

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # pragma: no cover
        # Nothing to clean up; context manager exists for ergonomic symmetry.
        return None

    def invoke(
        self,
        prompt: str,
        *,
        parser: Callable[[str], T] | None = None,
        workdir: str | None = None,
    ) -> Response[T]:
        effective_cwd = workdir if workdir is not None else self.workdir
        response = self._agent.invoke(
            prompt, session_id=self.session_id, parser=parser, workdir=effective_cwd
        )
        if self.session_id is None:
            self.session_id = response.session_id
        return response
