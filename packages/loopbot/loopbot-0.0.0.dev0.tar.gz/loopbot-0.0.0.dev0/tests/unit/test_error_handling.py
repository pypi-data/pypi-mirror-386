from __future__ import annotations

import pytest
from pydantic import BaseModel

from loopbot.errors import CliExitError
from loopbot.structured import _extract_and_parse_json


class _User(BaseModel):
    name: str


def test_extract_and_parse_json_raises_when_no_code_fence() -> None:
    """If no JSON code fence is present, raise a clear ValueError."""
    text = "Here is some prose without a JSON block."
    with pytest.raises(ValueError) as exc:
        _extract_and_parse_json(text, _User)
    assert "No JSON code fence" in str(exc.value)


def test_cli_exit_error_exposes_details() -> None:
    """CliExitError should carry return code and stderr details for debugging."""
    err = CliExitError(
        "OpenCode CLI exited", return_code=127, stderr="command not found"
    )
    assert isinstance(err, CliExitError)
    assert err.return_code == 127
    assert "command not found" in err.stderr
    # The string form should include the message passed to the constructor
    assert "OpenCode CLI exited" in str(err)
