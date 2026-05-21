from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import logfire

from schemas.review import SendConfirmation

REVIEW_RECIPIENT = "human-review-team@research-pipeline.internal"


def send_for_human_review(case_id: str, reason: str) -> SendConfirmation:
    """Send a research case for human review.

    Call this tool when the research output does not meet quality standards
    and requires human evaluation. Do not call this tool if quality signals
    are satisfactory.

    Args:
        case_id: The unique identifier of the research output to review.
        reason: A brief explanation of why this case requires human review.
    """
    confirmation = SendConfirmation(
        message_id=str(uuid4()),
        status="delivered",
        recipient=REVIEW_RECIPIENT,
        review_decision_id=case_id,
        timestamp=datetime.now(tz=timezone.utc),
    )
    logfire.info(
        "human_review.sent",
        case_id=case_id,
        reason=reason,
        message_id=confirmation.message_id,
        recipient=REVIEW_RECIPIENT,
        review_tool_called=True,
    )
    return confirmation


def log_no_review(case_id: str, reasoning: str) -> None:
    """Log that no human review was sent for a case.

    Called by the pipeline runner for every case where the review agent did NOT
    call send_for_human_review, ensuring every case has a recorded outcome.
    This is NOT an agent tool — it is called programmatically by pipeline/runner.py.

    Args:
        case_id: The unique identifier of the research output.
        reasoning: The agent's stated reasoning for not sending for review.
    """
    logfire.info(
        "human_review.not_sent",
        case_id=case_id,
        reasoning=reasoning,
        review_tool_called=False,
    )
