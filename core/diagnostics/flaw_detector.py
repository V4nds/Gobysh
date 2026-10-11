"""
Technical Flaw & Anomaly Diagnostics Framework for Goby v5.3.
Detects potential technical glitches and blindspots across 3 dimensions:
  1. Prompt / User Intent Flaws (internal contradictions, missing parameters, false premises)
  2. Project Topology & Architecture Flaws (double buttons/feature collisions, shallow seams)
  3. Logic & Layout UI Anomalies (text container overflow traps, unhandled async)
"""

from dataclasses import dataclass, field
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Set

from core.semantics.capability_registry import ComponentCapabilityRegistry


@dataclass
class TechnicalFlaw:
    """Represents an identified technical glitch, flaw, or anomaly."""
    dimension: str  # "prompt_intent" | "project_topology" | "logic_layout"
    severity: str    # "CRITICAL" | "HIGH" | "MEDIUM" | "ADVISORY"
    title: str
    description: str
    target_entity: Optional[str] = None
    suggested_fix: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "target_entity": self.target_entity,
            "suggested_fix": self.suggested_fix,
        }


class TechnicalFlawDetector:
    """
    Unified engine for diagnosing architectural, intent, and layout flaws.
    Enforces Single Source of Truth, layout elasticity, and contradiction resolution.
    """

    def __init__(self, capability_registry: Optional[ComponentCapabilityRegistry] = None):
        self.registry = capability_registry or ComponentCapabilityRegistry()

    def audit_prompt(self, prompt: str, repo_root: str = ".") -> List[TechnicalFlaw]:
        """
        Audits natural language prompt for internal contradictions,
        impossible constraints, or unverified claims.
        """
        flaws: List[TechnicalFlaw] = []
        p_lower = prompt.lower()

        # 1. Contradiction: Add/Modify X while forbidding touching X
        candidate_targets = re.findall(r"(?:tambah(?:kan)?|buat|add|create|export|ke|pada|di|to|in)\s+([a-zA-Z0-9_\.-]+)", p_lower)
        for target in candidate_targets:
            if target in ["fitur", "suatu", "sebuah", "the", "a", "an", "file"]:
                continue
            neg_pat = rf"(?:jangan|dilarang|don't|do not)\s+(?:ubah|sentuh|modify|touch)\s+(?:file\s+)?([a-zA-Z0-9_\.-]*{re.escape(target)}[a-zA-Z0-9_\.-]*)"
            m = re.search(neg_pat, p_lower)
            if m:
                flaws.append(
                    TechnicalFlaw(
                        dimension="prompt_intent",
                        severity="CRITICAL",
                        title="Contradictory Modification Constraint",
                        description=f"Prompt requests creating/modifying '{target}' while explicitly forbidding modifying '{m.group(1)}'.",
                        target_entity=target,
                        suggested_fix=f"Clarify scope boundary: either allow targeted changes to '{target}' or specify an external extension point.",
                    )
                )

        # 2. General negation contradiction ("tambahkan ... tapi jangan ubah file ... sama sekali")
        if re.search(r"(?:tambah|buat|implement).*?(?:tapi|namun|but)\s+(?:jangan|dilarang)\s+(?:ubah|sentuh).*?sama sekali", p_lower):
            if not any("Contradictory" in f.title for f in flaws):
                flaws.append(
                    TechnicalFlaw(
                        dimension="prompt_intent",
                        severity="CRITICAL",
                        title="Contradictory Total Immobility Constraint",
                        description="Prompt requests adding functionality while imposing total immobility on the target files.",
                        suggested_fix="Define which files are allowed to be modified or specify a new isolated file target.",
                    )
                )

        # 3. Missing critical parameters in destructive operations
        if any(w in p_lower for w in ["hapus", "delete", "drop", "reset"]) and not any(ext in p_lower for ext in [".py", ".ts", ".tsx", ".js", "tabel", "fitur"]):
            flaws.append(
                TechnicalFlaw(
                    dimension="prompt_intent",
                    severity="HIGH",
                    title="Ambiguous Destructive Intent",
                    description="Destructive action requested without specifying exact target entity or boundary.",
                    suggested_fix="Confirm exact target file, module, or database entity before executing delete.",
                )
            )

        return flaws

    def audit_topology(
        self,
        new_capabilities: Optional[List[Tuple[str, str]]] = None,
        existing_registry_files: Optional[List[str]] = None,
        target_files: Optional[List[str]] = None,
        repo_root: str = ".",
    ) -> List[TechnicalFlaw]:
        """
        Audits project architecture and UI surface topology for:
        - Double buttons / duplicate feature registrations (Capability Collision)
        - Broken Single Source of Truth
        """
        flaws: List[TechnicalFlaw] = []

        if new_capabilities:
            for cap, comp_file in new_capabilities:
                # Check if capability is already registered or implies duplicate control
                # In mock/existing files:
                if existing_registry_files:
                    for ex_file in existing_registry_files:
                        if ex_file != comp_file:
                            flaws.append(
                                TechnicalFlaw(
                                    dimension="project_topology",
                                    severity="HIGH",
                                    title="Capability Collision (Double Control / Duplicate Feature)",
                                    description=(
                                        f"Detected potential duplicate controls for capability '{cap}'. "
                                        f"It is already managed in '{ex_file}', but candidate attempts to mount in '{comp_file}'."
                                    ),
                                    target_entity=comp_file,
                                    suggested_fix=(
                                        f"Mount controls in the primary '{ex_file}' or reuse existing actions "
                                        f"to maintain Single Source of Truth (SSOT)."
                                    ),
                                )
                            )

        return flaws

    def audit_code_and_layout(self, code_str: str, file_path: str = "") -> List[TechnicalFlaw]:
        """
        Audits source code or layout templates (JSX/HTML/CSS) for UI and runtime logic flaws:
        - Text overflowing container bounds (fixed height container trap)
        - Double button handlers
        - Unhandled async promises
        """
        flaws: List[TechnicalFlaw] = []

        # 1. UI Layout Defect: Fixed height container with non-wrapping or dynamic text
        fixed_height_box = re.search(r'className=["\'][^"\']*(?:h-\d+|height:\s*\d+px)[^"\']*["\']', code_str)
        has_nowrap = bool(re.search(r'className=["\'][^"\']*(?:whitespace-nowrap|truncate|overflow-hidden)[^"\']*["\']', code_str))
        has_p_text = bool(re.search(r'<p[^>]*>.*?</p>', code_str, re.DOTALL))

        if fixed_height_box and (has_nowrap or has_p_text):
            # Check if there is missing dynamic scroll or wrapping
            if "overflow-auto" not in code_str and "flex-wrap" not in code_str:
                flaws.append(
                    TechnicalFlaw(
                        dimension="logic_layout",
                        severity="MEDIUM",
                        title="UI Layout Text Overflow Vulnerability",
                        description=(
                            "Detected fixed-height container enclosing text content without dynamic auto-wrap or scroll. "
                            "Risk of text overflowing the background card or being truncated awkwardly."
                        ),
                        target_entity=file_path,
                        suggested_fix="Use min-height (min-h-*) with dynamic flex-wrap, or add overflow-y-auto to allow content elasticity.",
                    )
                )

        # 2. Logic Defect: Unhandled async Promise without try/catch or .catch()
        if "async " in code_str and "await " in code_str:
            if "try {" not in code_str and "try:" not in code_str and ".catch(" not in code_str:
                flaws.append(
                    TechnicalFlaw(
                        dimension="logic_layout",
                        severity="MEDIUM",
                        title="Unhandled Asynchronous Error Boundary",
                        description="Async/await operation discovered without enclosing try/catch block or promise rejection handler.",
                        target_entity=file_path,
                        suggested_fix="Wrap async operations in try/catch and handle transient network/runtime failures.",
                    )
                )

        return flaws
