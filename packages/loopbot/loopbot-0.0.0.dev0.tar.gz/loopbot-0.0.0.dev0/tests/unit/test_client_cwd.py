from unittest.mock import patch

import pytest

from loopbot.client import AsyncOpenCodeClient
from loopbot.permissions import Permission


@pytest.mark.asyncio
@patch("loopbot.client.stream_opencode_cli")
async def test_client_passes_cwd_to_cli(mock_stream):
    async def gen():
        if False:
            yield {}  # pragma: no cover

    mock_stream.return_value = gen()

    c = AsyncOpenCodeClient(model="m", permission=Permission(), workdir="/work/a")
    # No events, just force iteration to trigger the call
    async for _ in c.stream("hello"):
        pass

    assert mock_stream.call_count == 1
    kwargs = mock_stream.call_args.kwargs
    assert kwargs.get("cwd") == "/work/a"
