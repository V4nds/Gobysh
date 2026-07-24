"""
Goby Core Module: Meta-Cognitive Engine for Autonomous AI Agents.
Provides Loop Detection Engine (LDE), Grounded Compiler Arbitrage (GCA),
Persistent State Memory, Multitasking Agent Orchestration,
and Cognitive Control Room (CCR) for pre-output validation.
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

__version__ = "1.1.0"
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
]
