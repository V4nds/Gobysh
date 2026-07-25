"""
Goby Core Module: Meta-Cognitive Engine for Autonomous AI Agents.
Provides Loop Detection Engine (LDE), Grounded Compiler Arbitrage (GCA),
Persistent State Memory, Multitasking Agent Orchestration,
Cognitive Control Room (CCR), and Closed-Loop Refinement Engine.
"""

from .lde_detector import LoopDetectionEngine, LoopAnalysisResult
from .gca_runner import GroundedCompilerArbitrage, ExecutionResult
from .state_memory import StateMemoryManager
from .orchestrator import MultitaskOrchestrator, TaskSpec, TaskStatus
from .session_briefing import SessionBriefingEngine
from .ccr_engine import (
    CognitiveControlRoom,
    NeuronSignal,
    ThoughtRecord,
    ContextAssessment,
    GateType,
    TriageLevel,
    ContextTier,
)
from .output_parsers import (
    StructuredTestResult,
    TestFailureDetail,
    BaseOutputParser,
    PytestParser,
    JestParser,
    GenericParser,
    detect_runner,
    get_parser,
)
from .failure_memory import FailurePatternStore, FailureFingerprint
from .refinement_loop import CCRRefinementLoop, RefinementResult
from . import cli

__version__ = "1.3.0"
__all__ = [
    "LoopDetectionEngine",
    "LoopAnalysisResult",
    "GroundedCompilerArbitrage",
    "ExecutionResult",
    "StateMemoryManager",
    "MultitaskOrchestrator",
    "TaskSpec",
    "TaskStatus",
    "SessionBriefingEngine",
    "CognitiveControlRoom",
    "NeuronSignal",
    "ThoughtRecord",
    "ContextAssessment",
    "GateType",
    "TriageLevel",
    "ContextTier",
    "StructuredTestResult",
    "TestFailureDetail",
    "BaseOutputParser",
    "PytestParser",
    "JestParser",
    "GenericParser",
    "detect_runner",
    "get_parser",
    "FailurePatternStore",
    "FailureFingerprint",
    "CCRRefinementLoop",
    "RefinementResult",
]
