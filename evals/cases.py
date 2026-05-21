from __future__ import annotations

import dataclasses
import json
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class EvalCase:
    topic: str
    label: str  # "pass", "borderline", or "fail"
    expected_composite: float
    expected_signals: dict[str, float]


def load_cases() -> list[EvalCase]:
    """Load eval cases from data/ground_truth.json."""
    path = Path(__file__).parent.parent / "data" / "ground_truth.json"
    data = json.loads(path.read_text())
    return [
        EvalCase(
            topic=topic,
            label=entry["label"],
            expected_composite=entry["expected_composite"],
            expected_signals=entry["expected_signals"],
        )
        for topic, entry in data.items()
    ]


CASES: list[EvalCase] = load_cases()
