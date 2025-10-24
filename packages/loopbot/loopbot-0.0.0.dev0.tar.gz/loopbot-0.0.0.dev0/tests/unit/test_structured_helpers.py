import pytest
from pydantic import BaseModel

from loopbot.structured import build_structured_prompt, create_structured_parser


class User(BaseModel):
    name: str
    age: int


def test_build_structured_prompt_includes_schema_bits():
    prompt = build_structured_prompt("Extract user", User)
    # Should contain field names and schema delimiters
    assert "<schema>" in prompt and "</schema>" in prompt
    assert "name" in prompt and "age" in prompt


def test_create_structured_parser_parses_fenced_json():
    parser = create_structured_parser(User)
    text = 'Here is the result:\n\n```json\n{\n  "name": "Alice", "age": 30\n}\n```\n'
    user = parser(text)
    assert user.name == "Alice"
    assert user.age == 30
