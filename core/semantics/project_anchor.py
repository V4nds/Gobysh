"""
Project Identity Anchor & Selective Reference Synthesizer for Goby v5.6.
Provides Ground of Being invariants to prevent AI agents from identity drift
and overhauling repository orientation when given external references.
"""

from dataclasses import dataclass, field
import os
import re
from typing import Any, Dict, List, Optional, Set


@dataclass
class ProjectIdentity:
    """Core Ground-of-Being definition for the active repository."""
    name: str
    version: str
    core_purpose: str
    foundational_modules: List[str] = field(default_factory=list)
    forbidden_drifts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "core_purpose": self.core_purpose,
            "foundational_modules": self.foundational_modules,
            "forbidden_drifts": self.forbidden_drifts,
        }


@dataclass
class ReferenceSynthesisResult:
    """3-Tier Selective Synthesis matrix for an external reference."""
    reference: str
    adopt_principles: List[str] = field(default_factory=list)
    adapt_targets: List[str] = field(default_factory=list)
    reject_bloat: List[str] = field(default_factory=list)
    guardrail_rule: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference": self.reference,
            "adopt_principles": self.adopt_principles,
            "adapt_targets": self.adapt_targets,
            "reject_bloat": self.reject_bloat,
            "guardrail_rule": self.guardrail_rule,
        }


class ProjectIdentityAnchor:
    """
    Guards repository identity invariants and provides selective 3-tier synthesis
    for any external references or integrations.
    """

    KNOWN_REFERENCE_TEMPLATES = [
        (
            r"rea\b|reverse[-_]engineer",
            [
                "Tri-state epistemic verification (Pass/Fail/Unknown, Unknown fails closed)",
                "Cryptographic evidence provenance (SHA-256 digests bound to test executions)",
                "Task obligation ledgers and fail-closed resolution gates",
            ],
            [
                "StateMemoryManager (3-pillar exit gate)",
                "goby gate and Antigravity Stop lifecycle hooks",
                "Prompt Spider obligation tracker",
            ],
            [
                "Binary disassemblers / decompilers (Ghidra, JEB, Apktool)",
                "Dynamic runtime process tracing & Mach-O/ELF parsers",
                "Reverse engineering CLI workflows unrelated to AI code quality",
            ],
        ),
        (
            r"diagram[-_]design|editorial",
            [
                "Editorial schematic design principles (Target density 4/10)",
                "1px crisp hairline stroke standard (no heavy bulky borders)",
                "Focal accent discipline (1-2 focal accents max, avoid rainbow slop)",
            ],
            [
                "TasteSynthesisEngine / VisualDensityGovernor heuristics",
                "Prompt Spider standalone HTML/SVG architecture diagram generator",
            ],
            [
                "Direct copy-pasting of unrelated diagram types without context",
                "Complex client-side rendering JS dependencies",
            ],
        ),
    ]

    def __init__(self, repo_root: str = "."):
        self.repo_root = os.path.abspath(repo_root)
        self._identity: Optional[ProjectIdentity] = None

    def get_identity(self) -> ProjectIdentity:
        """Loads and caches the project identity from repository manifests."""
        if self._identity:
            return self._identity

        name = "Gobysh"
        version = "5.5.0"
        core_purpose = "Context Manager & Guardrail Framework untuk AI Coding Agent"
        foundational_modules = ["ccr_engine", "state_memory", "prompt_spider", "hooks", "taste_synthesis"]
        forbidden_drifts = [
            "Overhauling repository identity into an unrelated tool",
            "Deleting core CLI commands or state memory manager",
            "Bypassing CCR hard gates or mechanical lifecycle hooks",
        ]

        # Inspect pyproject.toml
        pyproject_path = os.path.join(self.repo_root, "pyproject.toml")
        if os.path.isfile(pyproject_path):
            try:
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    content = f.read()
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if name_match:
                    name = name_match.group(1)
                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                if desc_match:
                    core_purpose = desc_match.group(1)
                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if ver_match:
                    version = ver_match.group(1)
            except Exception:
                pass

        self._identity = ProjectIdentity(
            name=name,
            version=version,
            core_purpose=core_purpose,
            foundational_modules=foundational_modules,
            forbidden_drifts=forbidden_drifts,
        )
        return self._identity

    def synthesize_reference(self, reference_str: str) -> ReferenceSynthesisResult:
        """
        Analyzes an external reference through the 3-Tier Selective Synthesis matrix.
        Emits an actionable IDENTITY_PRESERVATION rule.
        """
        ref_clean = reference_str.strip()
        if not ref_clean:
            return ReferenceSynthesisResult(reference="", guardrail_rule="")

        identity = self.get_identity()
        matched_adopt: List[str] = []
        matched_adapt: List[str] = []
        matched_reject: List[str] = []

        # Check known reference templates
        for pat, adopts, adapts, rejects in self.KNOWN_REFERENCE_TEMPLATES:
            if re.search(pat, ref_clean, re.IGNORECASE):
                matched_adopt = adopts
                matched_adapt = adapts
                matched_reject = rejects
                break

        # Fallback for generic external references
        if not matched_adopt:
            matched_adopt = [
                "Extract architectural invariants, quality criteria, and high-leverage abstractions",
            ]
            matched_adapt = [
                f"Integrate selectively into existing {identity.name} modules without altering public API contracts",
            ]
            matched_reject = [
                "Foreign dependencies, redundant monolithic sub-systems, and alien paradigms",
            ]

        # Synthesize rule
        rule = (
            f"IDENTITY_PRESERVATION [{identity.name}]: External reference '{ref_clean}' must be synthesized selectively: "
            f"1) ADOPT: {'; '.join(matched_adopt[:2])}. "
            f"2) ADAPT: {'; '.join(matched_adapt[:2])}. "
            f"3) REJECT: {'; '.join(matched_reject[:2])}. "
            f"Do NOT overhaul repository orientation '{identity.core_purpose}' or delete foundational primitives."
        )

        return ReferenceSynthesisResult(
            reference=ref_clean,
            adopt_principles=matched_adopt,
            adapt_targets=matched_adapt,
            reject_bloat=matched_reject,
            guardrail_rule=rule,
        )
