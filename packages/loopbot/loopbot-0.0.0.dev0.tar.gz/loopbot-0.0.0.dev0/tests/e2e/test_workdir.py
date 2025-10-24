import os
from pathlib import Path

import pytest

from loopbot import Agent, Permission, Response
from loopbot.events import ToolUseEvent

MODEL = os.environ.get("LOOPBOT_MODEL", "anthropic/claude-haiku-4-5")


def _combined_output(resp: Response[str]) -> str:
    tool_out = "\n".join(
        e.part.state.output for e in resp.events if isinstance(e, ToolUseEvent)
    )
    return ((resp.raw_text or "") + "\n" + tool_out).strip()


@pytest.mark.e2e
def test_workdir_controls_tool_cwd(tmp_path: Path) -> None:
    if not os.environ.get("LOOPBOT_E2E"):
        pytest.skip("Set LOOPBOT_E2E=1 to run end-to-end tests.")

    # Create two subfolders with different words
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "word.txt").write_text("apple\n", encoding="utf-8")
    (b / "word.txt").write_text("banana\n", encoding="utf-8")

    prompt = (
        "Use the bash tool to run: cat word.txt\nReturn only the raw command output."
    )

    # Session-scoped working directory (apple)
    agent = Agent(
        model=MODEL,
        permission=Permission(
            bash=Permission.ALLOW, edit=Permission.DENY, webfetch=Permission.DENY
        ),
    )
    with agent.session(workdir=str(a)) as s:
        r1 = s.invoke(prompt)
        out1 = _combined_output(r1).lower()
        assert "apple" in out1 and "banana" not in out1

    # New session with different working directory (banana)
    with agent.session(workdir=str(b)) as s2:
        r2 = s2.invoke(prompt)
        out2 = _combined_output(r2).lower()
        assert "banana" in out2 and "apple" not in out2
