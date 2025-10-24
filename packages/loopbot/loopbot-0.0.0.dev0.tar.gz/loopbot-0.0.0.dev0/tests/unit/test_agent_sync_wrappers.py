import pytest

from loopbot.agent import Agent, AsyncAgent, Session
from loopbot.events import ToolUseEvent
from loopbot.permissions import Permission
from loopbot.response import Response


def _tool_event() -> ToolUseEvent:
    raw = {
        "type": "tool_use",
        "timestamp": 1,
        "sessionID": "ses_sync",
        "part": {
            "id": "prt_tool",
            "sessionID": "ses_sync",
            "messageID": "msg_1",
            "type": "tool",
            "callID": "call_1",
            "tool": "bash",
            "state": {
                "status": "completed",
                "input": {"command": "echo hi"},
                "output": "hi\n",
                "title": "echo hi",
                "metadata": {"exit": 0},
                "time": {"start": 1, "end": 1},
            },
        },
    }
    return ToolUseEvent.model_validate(raw)


def test_agent_session_and_wrappers(monkeypatch):
    """Cover Agent.__init__, Agent.session, and sync wrappers via monkeypatch."""
    agent = Agent(model="m", permission=Permission())

    # Patch the underlying async agent's invoke to avoid running loops/CLI
    async def fake_invoke(prompt: str, *, session_id=None, parser=None, workdir=None):
        return Response(
            output="ok", raw_text="ok", session_id="ses_sync", events=[_tool_event()]
        )

    async def fake_invoke_structured(
        prompt: str, *, model_cls=None, session_id=None, parser=None, workdir=None
    ):
        return Response(
            output={"x": 1}, raw_text="{}", session_id="ses_sync", events=[]
        )

    monkeypatch.setattr(
        agent._async_agent, "invoke", lambda *a, **k: fake_invoke(*a, **k)
    )
    monkeypatch.setattr(
        agent._async_agent,
        "invoke_structured",
        lambda *a, **k: fake_invoke_structured(*a, **k),
    )

    # Agent.invoke
    r1 = agent.invoke("hello")
    assert r1.output == "ok"
    # Agent.invoke_structured
    r2 = agent.invoke_structured("hello", model_cls=dict)  # model_cls unused by fake
    assert isinstance(r2.output, dict)

    # Session path and __enter__/invoke coverage
    with agent.session(workdir="/tmp/work") as s:
        assert isinstance(s, Session)
        r3 = s.invoke("ping")
        assert r3.session_id == "ses_sync"
        # Response.tool_events property
        assert len(r3.tool_events) == 1

    # Ensure default workdir passed through for sync path
    captured = {}

    async def fake_invoke_wd(
        prompt: str, *, session_id=None, parser=None, workdir=None
    ):
        captured["workdir"] = workdir
        return Response(
            output="ok", raw_text="ok", session_id="ses_sync", events=[_tool_event()]
        )

    agent2 = Agent(model="m", permission=Permission())
    monkeypatch.setattr(
        agent2._async_agent, "invoke", lambda *a, **k: fake_invoke_wd(*a, **k)
    )
    with agent2.session(workdir="/tmp/default-wd") as s2:
        s2.invoke("ping")
        assert captured["workdir"] == "/tmp/default-wd"
