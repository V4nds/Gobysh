"""
Consciousness Engine for Goby Framework.
This module triggers a reflective state when a problem is successfully solved (Exit Code 0).
It acts as the Meta-Cognitive brain, capturing the journey, "translating" it into abstract heuristics,
and saving it to the Universal Memory Store.
"""

from typing import Dict, Any, List
from .universal_memory import UniversalMemoryStore


class ConsciousnessEngine:
    """
    Epistemic Consciousness Engine.
    Observes successful executions and abstracts the specific solutions into universal heuristic memories.
    """

    def __init__(self, universal_store: UniversalMemoryStore = None):
        self.memory = universal_store or UniversalMemoryStore()
        # In a real scenario, this would be an LLM abstraction layer
        # For now, it uses heuristic string extraction based on common patterns.
        self.active = True

    def trigger_consciousness_reflection(
        self,
        final_successful_output: str,
        past_errors: List[Dict[str, str]],
        language: str = "python"
    ) -> None:
        """
        Called when GCA Runner hits a success (Exit Code 0).
        This pauses standard execution and enters a "Reflection Phase".
        """
        if not self.active or not past_errors:
            return  # No errors to learn from, it just worked first try.

        print("[Goby Consciousness] Success detected. Entering Meta-Cognitive Reflection Phase...")

        # Extract the primary problem we were trying to solve
        # Usually the most frequent or severe error in past_errors
        primary_error = self._identify_primary_root_problem(past_errors)
        if not primary_error:
            return
            
        error_type = primary_error.get("error_type", "UnknownError")
        error_output = primary_error.get("error_output", "")

        # "Translate" using the "LLM" (Simulated here)
        abstract_root_cause, universal_heuristic = self._simulate_llm_translation(
            error_type, error_output
        )

        # Crystallize into universal memory
        crystallized_memory = self.memory.crystallize_memory(
            error_output=error_output,
            error_type=error_type,
            abstract_root_cause=abstract_root_cause,
            universal_heuristic=universal_heuristic,
            language=language
        )

        print(f"[Goby Consciousness] Memory Crystallized: {crystallized_memory.memory_id}")
        print(f"  -> Heuristic Learned: {universal_heuristic}")

    def _identify_primary_root_problem(self, past_errors: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Looks at the history of errors and finds the most dominant one to learn from.
        """
        # For simplicity, just take the last error before success.
        return past_errors[-1]

    def _simulate_llm_translation(self, error_type: str, error_output: str) -> tuple[str, str]:
        """
        Simulates an LLM taking specific code errors and turning them into Universal Heuristics.
        """
        if "RecursionError" in error_type or "maximum recursion depth" in error_output:
            return (
                "Infinite depth topology without a base case or cyclic state.",
                "Topology Bypass: Deform recursive state to iterative loop with explicit stack."
            )
        elif "ModuleNotFoundError" in error_type or "ImportError" in error_type:
            return (
                "Missing structural dependency or axiom constraint violation.",
                "Axiom Shift: Inject required external package or mock the interface explicitly."
            )
        elif "Timeout" in error_type or "MemoryError" in error_type:
            return (
                "System 2 exhaustive search space overload (NP-Hard simulation).",
                "Heuristic Bypass: Break exact-search and use probabilistic/heuristic bounded approximation."
            )
        
        # Default fallback
        return (
            "Generic logical disconnect or unhandled state.",
            "Lateral Thinking (Cantor Bypass): Invert the current assumption and try an orthogonal approach."
        )
