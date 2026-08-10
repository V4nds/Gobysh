"""
Goby Core Module v4.0: Omni-Synthesis Cognitive Framework.

Lazy-loading architecture: Only imports what is actually used.
This prevents heavy modules (CCR with 9 neurons, output_parsers, etc.)
from loading when only lightweight components are needed.
"""

# ---------------------------------------------------------------------------
# Lightweight re-exports (always available, near-zero cost)
# ---------------------------------------------------------------------------
from .lde_detector import LoopDetectionEngine, LoopAnalysisResult, similarity_ratio
from .gca_runner import GroundedCompilerArbitrage, ExecutionResult
from .state_memory import StateMemoryManager

__version__ = "4.1.0"


def verify(code: str, language: str = "python", context: dict = None):
    """Top-level helper for Genuine Pre-Output In-Memory Verification."""
    from .ccr_engine import CognitiveControlRoom
    ccr = CognitiveControlRoom()
    return ccr.verify_candidate(code, language=language, context=context)


def create_evidence_contract(claim: str, code_or_file: str, language: str = "python", test_command: str = None):
    """Top-level helper for machine-verifiable Evidence Contract generation."""
    from .ccr_engine import CognitiveControlRoom
    ccr = CognitiveControlRoom()
    return ccr.create_evidence_contract(claim, code_or_file, language=language, test_command=test_command)


# ---------------------------------------------------------------------------
# Lazy accessors — heavy modules load on first access only
# ---------------------------------------------------------------------------
def __getattr__(name: str):
    """Lazy-load heavy modules to keep import footprint minimal."""

    _lazy_map = {
        # CCR Engine (44KB, heaviest module)
        "CognitiveControlRoom": (".ccr_engine", "CognitiveControlRoom"),
        "NeuronSignal":         (".ccr_engine", "NeuronSignal"),
        "ThoughtRecord":        (".ccr_engine", "ThoughtRecord"),
        "ContextAssessment":    (".ccr_engine", "ContextAssessment"),
        "GateType":             (".ccr_engine", "GateType"),
        "TriageLevel":          (".ccr_engine", "TriageLevel"),
        "ContextTier":          (".ccr_engine", "ContextTier"),

        # Orchestrator
        "MultitaskOrchestrator": (".orchestrator", "MultitaskOrchestrator"),
        "TaskSpec":              (".orchestrator", "TaskSpec"),
        "TaskStatus":            (".orchestrator", "TaskStatus"),

        # Output Parsers (13KB)
        "StructuredTestResult": (".output_parsers", "StructuredTestResult"),
        "TestFailureDetail":    (".output_parsers", "TestFailureDetail"),
        "BaseOutputParser":     (".output_parsers", "BaseOutputParser"),
        "PytestParser":         (".output_parsers", "PytestParser"),
        "JestParser":           (".output_parsers", "JestParser"),
        "GenericParser":        (".output_parsers", "GenericParser"),
        "detect_runner":        (".output_parsers", "detect_runner"),
        "get_parser":           (".output_parsers", "get_parser"),

        # Failure Memory (legacy, still used by refinement_loop)
        "FailurePatternStore":  (".failure_memory", "FailurePatternStore"),
        "FailureFingerprint":   (".failure_memory", "FailureFingerprint"),

        # Refinement Loop
        "CCRRefinementLoop":    (".refinement_loop", "CCRRefinementLoop"),
        "RefinementResult":     (".refinement_loop", "RefinementResult"),

        # Session Briefing
        "SessionBriefingEngine": (".session_briefing", "SessionBriefingEngine"),

        # v3.0 Consciousness & Universal Memory
        "ConsciousnessEngine":   (".consciousness_engine", "ConsciousnessEngine"),
        "UniversalMemoryStore":  (".universal_memory", "UniversalMemoryStore"),
        "UniversalMemoryPattern":(".universal_memory", "UniversalMemoryPattern"),

        # v4.0 Omni-Synthesis & Evolution
        "OmniSynthesisEngine":   (".omni_synthesis", "OmniSynthesisEngine"),
        "SynthesisResult":       (".omni_synthesis", "SynthesisResult"),
        "SelfEvolutionEngine":   (".evolution_loop", "SelfEvolutionEngine"),
        
        # Taste Synthesis (Right Brain)
        "TasteSynthesisEngine":  (".taste_synthesis", "TasteSynthesisEngine"),
        "TasteEvaluation":       (".taste_synthesis", "TasteEvaluation"),
    }

    if name in _lazy_map:
        module_path, attr_name = _lazy_map[name]
        import importlib
        module = importlib.import_module(module_path, package=__name__)
        return getattr(module, attr_name)

    raise AttributeError(f"module 'core' has no attribute {name!r}")


__all__ = [
    # Always loaded
    "LoopDetectionEngine", "LoopAnalysisResult", "similarity_ratio",
    "GroundedCompilerArbitrage", "ExecutionResult",
    "StateMemoryManager",
    # Lazy loaded
    "CognitiveControlRoom", "NeuronSignal", "ThoughtRecord",
    "ContextAssessment", "GateType", "TriageLevel", "ContextTier",
    "MultitaskOrchestrator", "TaskSpec", "TaskStatus",
    "StructuredTestResult", "TestFailureDetail", "BaseOutputParser",
    "PytestParser", "JestParser", "GenericParser", "detect_runner", "get_parser",
    "FailurePatternStore", "FailureFingerprint",
    "CCRRefinementLoop", "RefinementResult",
    "SessionBriefingEngine",
    "ConsciousnessEngine", "UniversalMemoryStore", "UniversalMemoryPattern",
    "OmniSynthesisEngine", "SynthesisResult", "SelfEvolutionEngine",
    "TasteSynthesisEngine", "TasteEvaluation",
]
