from __future__ import annotations

import json
from pathlib import Path

import logfire

from agents.research_agent import run_research_agent
from agents.review_agent import run_review_agent
from schemas.experiment import ExperimentTrial
from schemas.research import ResearchCondition
from schemas.review import ReviewCondition
from tools.human_review import log_no_review

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()

_GROUND_TRUTH: dict = json.loads(
    (Path(__file__).parent.parent / "data" / "ground_truth.json").read_text()
)


async def run_trial(
    topic: str,
    research_condition: ResearchCondition,
    review_condition: ReviewCondition,
) -> ExperimentTrial:
    """Execute a single pipeline trial (Agent 1 → Agent 2) with Logfire instrumentation.

    Every trial produces a recorded outcome regardless of whether
    send_for_human_review is called.
    """
    trial = ExperimentTrial(
        topic=topic,
        research_condition=research_condition,
        review_condition=review_condition,
    )
    gt_label = _GROUND_TRUTH.get(topic, {}).get("label", "unknown")

    with logfire.span(
        "pipeline_trial",
        trial_id=trial.id,
        topic=topic,
        research_condition=str(research_condition),
        review_condition=str(review_condition),
        ground_truth_label=gt_label,
    ):
        research_output = await run_research_agent(topic, research_condition)
        trial.research_output = research_output

        review_decision, tool_called = await run_review_agent(
            research_output, review_condition
        )
        trial.review_decision = review_decision
        trial.review_tool_called = tool_called

        if not tool_called:
            log_no_review(research_output.id, review_decision.reasoning)

    return trial
