"""
Closed-Loop Auto-Refinement Engine for Goby Framework.
Connects CCR Hard-Gates, LDE Preemptive Match, and Failure Store
into a self-healing refinement loop.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .ccr_engine import CognitiveControlRoom, NeuronSignal
from .failure_memory import FailurePatternStore
from .lde_detector import LoopDetectionEngine


@dataclass
class RefinementResult:
    is_resolved: bool
    blocked_by_hard_gate: bool
    attempts: int
    final_code: str
    signals: List[NeuronSignal] = field(default_factory=list)
    hard_failures: List[Dict[str, Any]] = field(default_factory=list)
    action_taken: str = ""


class CCRRefinementLoop:
    """
    Automates the CCR -> LDE -> Failure Memory -> Re-eval loop.
    """

    def __init__(
        self,
        ccr: Optional[CognitiveControlRoom] = None,
        lde: Optional[LoopDetectionEngine] = None,
        failure_store: Optional[FailurePatternStore] = None,
        max_attempts: int = 2,
    ):
        self.ccr = ccr or CognitiveControlRoom()
        self.failure_store = failure_store or FailurePatternStore()
        self.lde = lde or LoopDetectionEngine(failure_store=self.failure_store)
        self.max_attempts = max_attempts

    def run_refinement_cycle(
        self, code: str, attempts_so_far: int = 1, expected_behavior: Optional[Dict[str, Any]] = None
    ) -> RefinementResult:
        """
        Evaluates a single attempt of code. If it fails a hard gate, it queries LDE.
        The AI agent must iteratively provide new code in subsequent calls.
        """
        signals = []
        syntax_sig = self.ccr.neuron_syntax_check(code)
        signals.append(syntax_sig)

        if syntax_sig.passed:
            scope_sig = self.ccr.neuron_scope_check(code)
            signals.append(scope_sig)
            
            # Since this is a UI checking capability, we should also check taste
            taste_sig = self.ccr.neuron_taste_design_check(code)
            signals.append(taste_sig)

        eval_res = self.ccr.evaluate_signals(signals)

        if not eval_res["blocked"]:
            return RefinementResult(
                is_resolved=True,
                blocked_by_hard_gate=False,
                attempts=attempts_so_far,
                final_code=code,
                signals=signals,
                action_taken="PASSED_ALL_HARD_GATES",
            )

        # Hard gate failure — query LDE preemptive match
        preemptive = self.lde.check_preemptive(eval_res["summary"])
        if preemptive and preemptive.known_pattern:
            action = f"PREEMPTIVE_MATCH: {preemptive.known_pattern.solution_taken}"
        elif attempts_so_far >= self.max_attempts:
            action = "TRIGGER_META_SYSTEMIC_LEAP"
        else:
            action = f"BLOCKED_ATTEMPT_{attempts_so_far}"

        return RefinementResult(
            is_resolved=False,
            blocked_by_hard_gate=True,
            attempts=attempts_so_far,
            final_code=code,
            signals=signals,
            hard_failures=eval_res["hard_failures"],
            action_taken=action,
        )
