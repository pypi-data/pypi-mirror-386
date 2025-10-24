from __future__ import annotations

from pydantic import BaseModel


class UsageMetrics(BaseModel):
    total_cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
