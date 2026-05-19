from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel, Field


class ReviewCondition(StrEnum):
    control = "control"
    monitored = "monitored"
    unmonitored = "unmonitored"
    scheming_weak = "scheming_weak"
    scheming_strong = "scheming_strong"


class ReviewDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    research_output_id: str
    decision: Literal["approve", "reject", "flag"]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    agent_condition: ReviewCondition
    scheming_detected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SendConfirmation(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["sent", "delivered", "failed"]
    recipient: str
    review_decision_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
