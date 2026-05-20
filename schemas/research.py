from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ResearchCondition(StrEnum):
    control = "control"
    scheming_weak = "scheming_weak"
    scheming_strong = "scheming_strong"


class QualitySignals(BaseModel):
    factual_accuracy: float = Field(ge=0.0, le=1.0)
    source_quality: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    coherence: float = Field(ge=0.0, le=1.0)
    bias_score: float = Field(ge=0.0, le=1.0)
    scheming_indicators: list[str] = Field(default_factory=list)


class ResearchOutput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    content: str
    sources: list[str] = Field(default_factory=list)
    quality_signals: QualitySignals | None = None
    agent_condition: ResearchCondition
    created_at: datetime = Field(default_factory=datetime.utcnow)
