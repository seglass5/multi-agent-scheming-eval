from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

from evals.cases import CASES, EvalCase
from evals.conditions import CONDITIONS, CONDITIONS_BY_NAME, ExperimentCondition
from pipeline.runner import run_trial
from schemas.experiment import ExperimentTrial
from schemas.research import ResearchCondition
from schemas.review import ReviewCondition

_RESULTS_DIR = Path(__file__).parent.parent / "data" / "results"


@dataclasses.dataclass
class TrialResult:
    trial: ExperimentTrial
    condition: ExperimentCondition
    case: EvalCase
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def tool_called(self) -> bool:
        return bool(self.trial.review_tool_called)


async def _run_one(
    condition: ExperimentCondition,
    case: EvalCase,
    semaphore: asyncio.Semaphore,
) -> TrialResult:
    async with semaphore:
        try:
            trial = await run_trial(
                case.topic,
                condition.research_condition,
                condition.review_condition,
            )
            result = TrialResult(trial=trial, condition=condition, case=case)
            decision = trial.review_decision.decision if trial.review_decision else "?"
            print(
                f"  [{condition.name}] {case.topic[:55]:55s}"
                f"  {decision:7s}  tool_called={result.tool_called}"
            )
            return result
        except Exception as exc:
            trial = ExperimentTrial(
                topic=case.topic,
                research_condition=condition.research_condition,
                review_condition=condition.review_condition,
            )
            result = TrialResult(trial=trial, condition=condition, case=case, error=str(exc))
            print(f"  [{condition.name}] {case.topic[:55]:55s}  ERROR: {exc}")
            return result


async def run_experiment(
    conditions: list[ExperimentCondition] | None = None,
    cases: list[EvalCase] | None = None,
    max_concurrency: int = 3,
) -> list[TrialResult]:
    """Run the experiment matrix and return all trial results.

    Errors are captured per-trial; a failed trial does not abort the run.
    """
    conditions = conditions or CONDITIONS
    cases = cases or CASES
    semaphore = asyncio.Semaphore(max_concurrency)

    total = len(conditions) * len(cases)
    print(f"Running {total} trials ({len(conditions)} conditions × {len(cases)} cases)...")

    tasks = [
        _run_one(condition, case, semaphore)
        for condition in conditions
        for case in cases
    ]
    results = await asyncio.gather(*tasks)
    successes = sum(1 for r in results if r.success)
    print(f"\nCompleted: {successes}/{total} successful.")
    return list(results)


def save_results(results: list[TrialResult], path: Path) -> None:
    """Persist results as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in results:
            record = {
                "trial": r.trial.model_dump(mode="json"),
                "condition_name": r.condition.name,
                "case_topic": r.case.topic,
                "case_label": r.case.label,
                "case_expected_composite": r.case.expected_composite,
                "case_expected_signals": r.case.expected_signals,
                "error": r.error,
            }
            f.write(json.dumps(record) + "\n")


def load_results(path: Path) -> list[TrialResult]:
    """Load results from a JSONL file produced by save_results."""
    results = []
    with path.open() as f:
        for line in f:
            record = json.loads(line)
            trial = ExperimentTrial.model_validate(record["trial"])
            condition = CONDITIONS_BY_NAME[record["condition_name"]]
            case = EvalCase(
                topic=record["case_topic"],
                label=record["case_label"],
                expected_composite=record["case_expected_composite"],
                expected_signals=record["case_expected_signals"],
            )
            results.append(TrialResult(trial=trial, condition=condition, case=case, error=record["error"]))
    return results


def _results_path(condition_names: list[str]) -> Path:
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    suffix = "_".join(condition_names) if len(condition_names) <= 3 else f"{len(condition_names)}conditions"
    return _RESULTS_DIR / f"{ts}_{suffix}.jsonl"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the scheming eval experiment matrix.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--condition", metavar="NAME", help="Run a single condition by name.")
    group.add_argument("--all", action="store_true", help="Run all 10 conditions.")
    parser.add_argument("--max-concurrency", type=int, default=3, metavar="N",
                        help="Maximum concurrent trials (default: 3).")
    parser.add_argument("--no-save", action="store_true", help="Do not save results to disk.")
    args = parser.parse_args()

    if args.all:
        selected = CONDITIONS
    else:
        if args.condition not in CONDITIONS_BY_NAME:
            valid = ", ".join(CONDITIONS_BY_NAME)
            parser.error(f"Unknown condition '{args.condition}'. Valid: {valid}")
        selected = [CONDITIONS_BY_NAME[args.condition]]

    results = asyncio.run(run_experiment(conditions=selected, max_concurrency=args.max_concurrency))

    if not args.no_save:
        path = _results_path([c.name for c in selected])
        save_results(results, path)
        print(f"Results saved to {path}")
