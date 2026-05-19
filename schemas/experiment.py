from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from schemas.research import ResearchCondition, ResearchOutput
from schemas.review import ReviewCondition, ReviewDecision


class ExperimentTrial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    research_condition: ResearchCondition
    review_condition: ReviewCondition
    research_output: ResearchOutput | None = None
    review_decision: ReviewDecision | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
