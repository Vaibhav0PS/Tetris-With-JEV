"""Pydantic schemas for typed Jev AI decisions and actions."""

from typing import List, Optional
from pydantic import BaseModel, Field

from game.actions import TetrisAction


class JevDecision(BaseModel):
    """Structured decision returned by the Jev AI agent."""

    action: TetrisAction = Field(
        description="Choose exactly one action that should be executed next."
    )


class TetrisPlan(BaseModel):
    """Optional multi-action sequence plan for batch execution."""

    actions: List[TetrisAction] = Field(
        description="Ordered list of sequential actions to execute."
    )


class DecisionResult(BaseModel):
    """Enriched decision tracking model including performance and confidence metadata."""

    action: TetrisAction
    confidence: Optional[float] = None
    latency_ms: float = 0.0
    source: str = "jev"  # 'jev', 'fallback', 'heuristic', 'mock'
    error_message: Optional[str] = None
