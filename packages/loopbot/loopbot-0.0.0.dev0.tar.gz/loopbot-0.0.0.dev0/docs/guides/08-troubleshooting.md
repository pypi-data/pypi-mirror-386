# Troubleshooting

- "CLI not found": Ensure `opencode` is installed and on PATH.
- Empty text events: Some streams emit markers without payload; the SDK ignores these.
- Tool output missing: Inspect `Response.tool_events[*].part.state.output`.
- Session not remembered: Use `with agent.session()` or pass the captured `session_id`.
- Permission Denied Errors: If a tool command fails, verify the `Permission` object explicitly allows the action (e.g., `bash=Permission.ALLOW`).
