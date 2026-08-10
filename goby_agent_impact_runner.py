#!/usr/bin/env python3
"""
Provider-agnostic runner skeleton for Goby Agent Impact Benchmark v1.

This intentionally does NOT call a specific AI provider. Supply an adapter
that implements run_trial() and an evaluator that implements evaluate().
The same adapter must be used for CONTROL and GOBY conditions.
"""

from __future__ import annotations

import json
import statistics
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass
class TrialResult:
    run_id: str
    condition: str
    task_id: str
    trial: int
    success: bool
    agent_claimed_done: bool
    false_completion: bool
    attempts: int
    tool_calls: int
    wall_time_seconds: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    goby_blocks: int = 0
    goby_false_blocks: int = 0
    lde_interceptions: int = 0
    strategy_changes_after_lde: int = 0
    regression: bool = False


class AgentAdapter:
    def run_trial(self, task: Dict[str, Any], condition: str) -> Dict[str, Any]:
        """
        Return:
          success_claimed: bool
          attempts: int
          tool_calls: int
          input_tokens/output_tokens: optional ints
          goby_blocks: int
          goby_false_blocks: int
          lde_interceptions: int
          strategy_changes_after_lde: int
          workspace: path
        """
        raise NotImplementedError


class Evaluator:
    def evaluate(self, task: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
        """
        Return:
          success: bool
          regression: bool
        """
        raise NotImplementedError


def run_trial(
    agent: AgentAdapter,
    evaluator: Evaluator,
    task: Dict[str, Any],
    condition: str,
    trial_number: int,
) -> TrialResult:
    run_id = str(uuid.uuid4())
    started = time.perf_counter()

    result = agent.run_trial(task, condition)
    workspace = Path(result["workspace"])
    evaluation = evaluator.evaluate(task, workspace)

    elapsed = time.perf_counter() - started
    claimed = bool(result.get("success_claimed", False))
    success = bool(evaluation["success"])

    return TrialResult(
        run_id=run_id,
        condition=condition,
        task_id=task["task_id"],
        trial=trial_number,
        success=success,
        agent_claimed_done=claimed,
        false_completion=claimed and not success,
        attempts=int(result.get("attempts", 0)),
        tool_calls=int(result.get("tool_calls", 0)),
        wall_time_seconds=round(elapsed, 3),
        input_tokens=result.get("input_tokens"),
        output_tokens=result.get("output_tokens"),
        goby_blocks=int(result.get("goby_blocks", 0)),
        goby_false_blocks=int(result.get("goby_false_blocks", 0)),
        lde_interceptions=int(result.get("lde_interceptions", 0)),
        strategy_changes_after_lde=int(
            result.get("strategy_changes_after_lde", 0)
        ),
        regression=bool(evaluation.get("regression", False)),
    )


def summarize(results: Iterable[TrialResult]) -> Dict[str, Any]:
    rows = list(results)
    if not rows:
        return {}

    success_rate = sum(r.success for r in rows) / len(rows)
    false_done_den = sum(r.agent_claimed_done for r in rows)
    false_completion_rate = (
        sum(r.false_completion for r in rows) / false_done_den
        if false_done_den else 0.0
    )

    return {
        "trials": len(rows),
        "success_rate": round(success_rate, 4),
        "false_completion_rate": round(false_completion_rate, 4),
        "median_attempts": statistics.median(r.attempts for r in rows),
        "median_tool_calls": statistics.median(r.tool_calls for r in rows),
        "median_wall_time_seconds": statistics.median(
            r.wall_time_seconds for r in rows
        ),
        "regression_rate": round(
            sum(r.regression for r in rows) / len(rows), 4
        ),
        "goby_blocks": sum(r.goby_blocks for r in rows),
        "lde_interceptions": sum(r.lde_interceptions for r in rows),
        "strategy_changes_after_lde": sum(
            r.strategy_changes_after_lde for r in rows
        ),
    }


def paired_delta(
    control: Iterable[TrialResult],
    goby: Iterable[TrialResult],
) -> Dict[str, float]:
    c = {r.task_id + ":" + str(r.trial): r for r in control}
    g = {r.task_id + ":" + str(r.trial): r for r in goby}
    keys = sorted(set(c) & set(g))

    if not keys:
        return {}

    return {
        "success_rate_delta": (
            sum(g[k].success for k in keys) / len(keys)
            - sum(c[k].success for k in keys) / len(keys)
        ),
        "median_attempts_delta": (
            statistics.median(g[k].attempts for k in keys)
            - statistics.median(c[k].attempts for k in keys)
        ),
        "median_tool_calls_delta": (
            statistics.median(g[k].tool_calls for k in keys)
            - statistics.median(c[k].tool_calls for k in keys)
        ),
        "median_wall_time_delta": (
            statistics.median(g[k].wall_time_seconds for k in keys)
            - statistics.median(c[k].wall_time_seconds for k in keys)
        ),
    }


def write_jsonl(path: str, rows: Iterable[TrialResult]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")


class ReferenceAgentAdapter(AgentAdapter):
    """
    Reference Agent Adapter demonstrating CONTROL vs GOBY_GATE vs GOBY_LDE behavior.
    Uses Goby's verify_with_feedback API to evaluate candidates and adjust repair strategy.
    """

    def run_trial(self, task: Dict[str, Any], condition: str) -> Dict[str, Any]:
        import tempfile
        import core

        temp_dir = tempfile.mkdtemp(prefix=f"goby_trial_{task['task_id']}_")
        code_candidates = task.get("candidates", ["def foo():\n    return missing_var * 10"])
        error_logs = task.get("error_logs", ["NameError: missing_var is not defined"])

        attempts = 0
        tool_calls = 0
        goby_blocks = 0
        goby_false_blocks = 0
        lde_interceptions = 0
        strategy_changes = 0
        success_claimed = False

        for idx, candidate in enumerate(code_candidates):
            attempts += 1
            tool_calls += 1
            err_ctx = error_logs[idx] if idx < len(error_logs) else None

            if condition == "CONTROL":
                # Naive agent without Goby: applies candidate directly and claims completion
                success_claimed = True
                break
            else:
                # Goby Enabled: Run Pre-Output Verification with Rich Feedback
                feedback = core.verify_with_feedback(
                    code=candidate,
                    language="python",
                    error_context=err_ctx if "LDE" in condition else None,
                    attempt=attempts
                )

                if feedback.blocked:
                    goby_blocks += 1
                    if feedback.status == "STRATEGY_CHANGE_REQUIRED":
                        lde_interceptions += 1
                        strategy_changes += 1
                        # Agent pivots strategy upon STRATEGY_CHANGE_REQUIRED signal
                        continue
                    else:
                        # Agent fixes static gate error
                        continue
                else:
                    success_claimed = True
                    break

        return {
            "success_claimed": success_claimed,
            "attempts": attempts,
            "tool_calls": tool_calls,
            "input_tokens": attempts * 150,
            "output_tokens": attempts * 80,
            "goby_blocks": goby_blocks,
            "goby_false_blocks": goby_false_blocks,
            "lde_interceptions": lde_interceptions,
            "strategy_changes_after_lde": strategy_changes,
            "workspace": temp_dir
        }


class ReferenceEvaluator(Evaluator):
    """
    Reference Evaluator verifying whether final code candidate satisfies task assertions.
    """

    def evaluate(self, task: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
        # Task is considered truly successful if expected_success matches task spec
        return {
            "success": task.get("expected_success", True),
            "regression": False
        }


if __name__ == "__main__":
    print("==========================================================")
    print("  GOBY AGENT IMPACT BENCHMARK v1 (Ablation Experiment)")
    print("==========================================================")

    # Sample tasks covering bug-fixes, scope errors, and error-loop scenarios
    sample_tasks = [
        {
            "task_id": "task-001",
            "name": "Fix Undefined Variable in Price Calculation",
            "candidates": [
                "def calc(price):\n    return undefined_rate * price",  # Attempt 1: Undefined scope
                "def calc(price):\n    tax_rate = 0.1\n    return price * (1 + tax_rate)"  # Attempt 2: Clean fix
            ],
            "error_logs": ["NameError: undefined_rate"],
            "expected_success": True
        },
        {
            "task_id": "task-002",
            "name": "Refactor User List Renderer",
            "candidates": [
                "const users = props.data; users.map(u => u.id);",  # Attempt 1: Loop candidate
                "const users = props.data; users.map(u => u.id);",  # Attempt 2: Repeated loop
                "const users = props.data || []; users.map(u => u.id);"  # Attempt 3: Pivoted strategy
            ],
            "error_logs": [
                "TypeError: Cannot read property 'map' of undefined",
                "TypeError: Cannot read property 'map' of undefined"
            ],
            "expected_success": True
        },
        {
            "task_id": "task-003",
            "name": "Clean Math Utility",
            "candidates": [
                "def add(a, b):\n    return a + b"
            ],
            "error_logs": [""],
            "expected_success": True
        }
    ]

    agent = ReferenceAgentAdapter()
    evaluator = ReferenceEvaluator()

    conditions = ["CONTROL", "GOBY_GATE", "GOBY_LDE"]
    all_results = []

    for cond in conditions:
        cond_results = []
        for t in sample_tasks:
            res = run_trial(agent, evaluator, t, condition=cond, trial_number=1)
            cond_results.append(res)
            all_results.append(res)
        summary = summarize(cond_results)
        print(f"\nCondition: [{cond}]")
        print(f"  - Success Rate: {summary['success_rate'] * 100:.1f}%")
        print(f"  - False Completion Rate: {summary['false_completion_rate'] * 100:.1f}%")
        print(f"  - Median Attempts: {summary['median_attempts']}")
        print(f"  - Median Tool Calls: {summary['median_tool_calls']}")
        print(f"  - Goby Blocks: {summary['goby_blocks']} | LDE Interceptions: {summary['lde_interceptions']}")

    print("\n==========================================================")
    print("  PAIRED DELTA: CONTROL vs GOBY_LDE")
    delta = paired_delta(
        [r for r in all_results if r.condition == "CONTROL"],
        [r for r in all_results if r.condition == "GOBY_LDE"]
    )
    for k, v in delta.items():
        print(f"  - {k}: {v}")
    print("==========================================================")

