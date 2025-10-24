import pytest

from loopbot.agent import AsyncAgent
from loopbot.permissions import Permission
from loopbot.response import Response


@pytest.mark.asyncio
async def test_async_session_invoke_updates_session_id(monkeypatch):
    async_agent = AsyncAgent(model="m", permission=Permission())

    async def fake_invoke(prompt: str, *, session_id=None, parser=None, workdir=None):
        return Response(output="x", raw_text="x", session_id="ses_async", events=[])

    monkeypatch.setattr(async_agent, "invoke", fake_invoke)

    session = async_agent.session()
    # __init__ executed; now call invoke
    resp = await session.invoke("hello")
    assert resp.session_id == "ses_async"
    assert session.session_id == "ses_async"


@pytest.mark.asyncio
async def test_async_session_default_workdir(monkeypatch, tmp_path):
    async_agent = AsyncAgent(model="m", permission=Permission())

    seen = {}

    async def fake_invoke(prompt: str, *, session_id=None, parser=None, workdir=None):
        seen["workdir"] = workdir
        return Response(output="x", raw_text="x", session_id="ses_async", events=[])

    monkeypatch.setattr(async_agent, "invoke", fake_invoke)

    default = tmp_path / "a"
    default.mkdir()
    session = async_agent.session(workdir=str(default))

    await session.invoke("hello")
    assert seen["workdir"] == str(default)

    override = tmp_path / "b"
    override.mkdir()
    await session.invoke("hello", workdir=str(override))
    assert seen["workdir"] == str(override)
