from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Regex to find a JSON block within a markdown code fence
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def build_structured_prompt(prompt: str, model_cls: type[T]) -> str:
    """Decorate a user prompt with explicit JSON schema instructions.

    This keeps the core agent simple while enabling structured outputs as a
    composable layer.
    """
    schema = json.dumps(model_cls.model_json_schema(), indent=2)
    return (
        f"{prompt}\n\n"
        "Please extract the information and provide a response in a JSON object "
        "within a markdown code fence.\n"
        "The JSON object must conform to the following schema:\n"
        "<schema>\n"
        f"{schema}\n"
        "</schema>\n"
    )


def _extract_and_parse_json(text: str, model_cls: type[T]) -> T:
    """Find a JSON code fence and validate it against the given Pydantic model."""
    match = JSON_FENCE_RE.search(text)
    if not match:
        raise ValueError("No JSON code fence found in the agent's response.")

    json_block = match.group(1)
    try:
        return model_cls.model_validate_json(json_block)
    except ValidationError as e:  # pragma: no cover - exercised via E2E
        raise ValueError(
            f"Failed to validate extracted JSON against {model_cls.__name__}."
        ) from e


def create_structured_parser(model_cls: type[T]) -> Callable[[str], T]:
    """Factory returning a parser that extracts and validates a JSON code block."""

    def parser(raw_text: str) -> T:
        return _extract_and_parse_json(raw_text, model_cls)

    return parser
