"""Async wrapper for invoking the OpenCode CLI and streaming JSON events.

This module shells out to the external CLI. We omit it from default coverage to
keep fast runs stable; E2E tests exercise this path when the CLI is available.
"""

from __future__ import annotations

import asyncio
import json
import os
from asyncio.subprocess import PIPE
from collections.abc import AsyncIterator
from typing import Any

from .errors import CliExitError, CliNotFoundError
from .permissions import Permission


def _build_command(prompt: str, model: str, session_id: str | None) -> list[str]:
    cmd = ["opencode", "run", "--format", "json", "--model", model]
    if session_id:
        cmd.extend(["--session", session_id])
    cmd.append(prompt)
    return cmd


def _build_env(
    permission: Permission, providers: dict[str, Any] | None
) -> dict[str, str]:
    # Merge with current env to avoid clobbering
    env = dict(os.environ)
    config: dict[str, Any] = {"permission": permission.to_dict()}
    if providers:
        config["provider"] = providers
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps(config)
    return env


async def stream_opencode_cli(
    prompt: str,
    *,
    model: str,
    permission: Permission,
    providers: dict[str, Any] | None,
    session_id: str | None,
    cwd: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Execute `opencode run` and yield parsed JSON lines.

    Yields only valid JSON objects. Non-JSON lines are ignored. On non-zero
    exit, raises `CliExitError`. If the executable is missing, raises
    `CliNotFoundError`.
    """

    command = _build_command(prompt, model, session_id)
    env = _build_env(permission, providers)

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            cwd=cwd,
        )
    except FileNotFoundError as e:  # pragma: no cover - requires missing binary
        raise CliNotFoundError(
            "The 'opencode' command was not found. Ensure it is installed and on PATH."
        ) from e

    assert proc.stdout is not None  # for type checkers
    assert proc.stderr is not None

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            # Skip non-JSON lines printed by the CLI
            continue
        else:
            yield obj

    rc = await proc.wait()
    if rc != 0:
        stderr_bytes = await proc.stderr.read()
        raise CliExitError(
            f"OpenCode CLI exited with code {rc}.",
            return_code=rc,
            stderr=stderr_bytes.decode("utf-8", errors="ignore"),
        )
