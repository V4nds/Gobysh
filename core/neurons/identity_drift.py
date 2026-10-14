"""
Neuron: Identity Drift & Project Boundary Protection for Goby v5.6.
Ensures that code candidates do not violate the core Ground of Being,
alter root package declarations, delete primary public API re-exports,
or inject foreign monolithic architectures into Goby.
"""

import os
import re
from typing import Any, Dict, List, Optional

from core.ccr_engine import NeuronSignal, GateType
from core.semantics.project_anchor import ProjectIdentityAnchor


ALIEN_MONOLITHIC_PATTERNS = [
    (r"\bclass\s+(?:BinaryDisassembler|ElfParser|MachOParser|AndroidApkDecompiler)\b", "alien_disassembler_runtime"),
    (r"\bdef\s+(?:disassemble_x86|decompile_apk|parse_elf_header)\b", "alien_binary_analysis_logic"),
]


def neuron_identity_drift_check(
    self,
    code: str,
    filepath: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> NeuronSignal:
    """
    Evaluates whether code violates the repository's Ground of Being invariants.
    HARD GATE: Blocks accidental project re-orientation, foundational export wiping,
    or alien monolithic code injection.
    """
    root = repo_root or getattr(self, "repo_root", None) or os.getcwd()
    anchor = ProjectIdentityAnchor(repo_root=root)
    identity = anchor.identity

    norm_path = filepath.replace("\\", "/").lower() if filepath else ""

    # 1. Check pyproject.toml / package definition integrity
    if "pyproject.toml" in norm_path or "setup.py" in norm_path:
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', code)
        if name_match:
            declared_name = name_match.group(1).lower()
            expected_prefix = identity.name.lower()
            if not (declared_name.startswith(expected_prefix) or expected_prefix.startswith(declared_name)):
                return NeuronSignal(
                    neuron_name="IDENTITY_DRIFT",
                    gate_type=GateType.HARD,
                    passed=False,
                    confidence=1.0,
                    message=(
                        f"Project name mutation detected in {filepath}: declared '{declared_name}', "
                        f"expected anchor identity '{identity.name}'. Re-orienting repository identity is forbidden."
                    ),
                    evidence={"declared_name": declared_name, "expected_identity": identity.name},
                    suggestion=f"Preserve root project identity '{identity.name}' as AI Context Manager & Guardrail Framework.",
                )

    # 2. Check core package re-exports integrity
    if norm_path.endswith("core/__init__.py") or norm_path.endswith("core\\__init__.py"):
        essential_exports = ["StateMemoryManager", "verify", "resolve_intent"]
        missing = [exp for exp in essential_exports if exp not in code]
        if missing:
            return NeuronSignal(
                neuron_name="IDENTITY_DRIFT",
                gate_type=GateType.HARD,
                passed=False,
                confidence=1.0,
                message=(
                    f"Foundational export(s) {missing} missing or deleted from core/__init__.py. "
                    "Primary public API surface must be preserved."
                ),
                evidence={"missing_exports": missing},
                suggestion="Retain foundational re-exports in core/__init__.py to prevent breaking downstream callers.",
            )

    # 3. Check for monolithic alien injection
    for pattern, reason in ALIEN_MONOLITHIC_PATTERNS:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            return NeuronSignal(
                neuron_name="IDENTITY_DRIFT",
                gate_type=GateType.HARD,
                passed=False,
                confidence=1.0,
                message=(
                    f"Code injection violates forbidden identity drift ({reason}): '{match.group(0)}'. "
                    f"Goby identity is '{identity.core_purpose}'. External domains must be adapted or rejected (Tier 3), "
                    "never pasted as monolithic foreign runtimes."
                ),
                evidence={"matched_pattern": pattern, "matched_text": match.group(0), "drift_reason": reason},
                suggestion="Adopt principles only; adapt integration into existing Goby modules (e.g. StateMemory, CCR) and reject foreign runtime bloat.",
            )

    return NeuronSignal(
        neuron_name="IDENTITY_DRIFT",
        gate_type=GateType.HARD,
        passed=True,
        confidence=1.0,
        message="Project identity invariants preserved.",
        evidence={"project": identity.name, "purpose": identity.core_purpose},
    )
