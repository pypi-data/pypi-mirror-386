"""Typed message and controller models for PenguiFlow."""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class Headers(BaseModel):
    tenant: str
    topic: str | None = None
    priority: int = 0


class Message(BaseModel):
    payload: Any
    headers: Headers
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = Field(default_factory=time.time)
    deadline_s: float | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """Represents a chunk of streamed output."""

    stream_id: str
    seq: int
    text: str
    done: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    kind: Literal["retrieve", "web", "sql", "summarize", "route", "stop"]
    args: dict[str, Any] = Field(default_factory=dict)
    max_concurrency: int = 1


class Thought(BaseModel):
    steps: list[PlanStep]
    rationale: str
    done: bool = False


class WM(BaseModel):
    query: str
    facts: list[Any] = Field(default_factory=list)
    hops: int = 0
    budget_hops: int | None = 8
    tokens_used: int = 0
    budget_tokens: int | None = None
    confidence: float = 0.0


class FinalAnswer(BaseModel):
    text: str
    citations: list[str] = Field(default_factory=list)


__all__ = [
    "Headers",
    "Message",
    "StreamChunk",
    "PlanStep",
    "Thought",
    "WM",
    "FinalAnswer",
]
