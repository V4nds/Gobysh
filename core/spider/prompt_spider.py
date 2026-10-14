"""
Prompt Spider Engine for Goby v5.3.
Crawls raw natural language user requests, classifies elements across 5 empirical tags,
integrates Technical Flaw Detection, and synthesizes 7-Pillar Empirical Blueprints
with Mechanical Contract Binding and Prompt Hash Invariants.
"""

from dataclasses import dataclass, field
import hashlib
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from core.spider.semantic_bridge import TripartiteSemanticBridge, NormalizedConcept, ResolvedASTEntity
from core.diagnostics.flaw_detector import TechnicalFlawDetector, TechnicalFlaw
from core.translation.scanner import RepositoryScanner
from core.translation.symbol_mapper import SymbolMap


@dataclass
class SpiderToken:
    """A tagged token/entity extracted from user prompt during crawling."""
    category: str  # "claim" | "owner" | "file" | "approval" | "vague"
    raw_text: str
    normalized_concept: str
    resolved_entity: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "raw_text": self.raw_text,
            "normalized_concept": self.normalized_concept,
            "resolved_entity": self.resolved_entity,
            "confidence": self.confidence,
        }


@dataclass
class ClarificationItem:
    """Structured clarification item generated for ambiguous (vague) tokens."""
    element: str
    question: str
    options: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element": self.element,
            "question": self.question,
            "options": self.options,
        }


@dataclass
class EmpiricalBlueprint:
    """The 7-Pillar Empirical Plan synthesized by Prompt Spider."""
    role: str
    objective: str
    context: Dict[str, Any]
    rules: List[str]
    review: List[str]
    start_step: str
    ship_criteria: List[str]
    tokens: List[SpiderToken] = field(default_factory=list)
    clarifications: List[ClarificationItem] = field(default_factory=list)
    detected_flaws: List[TechnicalFlaw] = field(default_factory=list)
    prompt_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "objective": self.objective,
            "context": self.context,
            "rules": self.rules,
            "review": self.review,
            "start_step": self.start_step,
            "ship_criteria": self.ship_criteria,
            "tokens": [t.to_dict() for t in self.tokens],
            "clarifications": [c.to_dict() for c in self.clarifications],
            "detected_flaws": [f.to_dict() for f in self.detected_flaws],
            "prompt_hash": self.prompt_hash,
        }

    def to_markdown(self) -> str:
        """Formats the blueprint into an actionable markdown implementation section."""
        lines = [
            f"# Empirical Execution Blueprint [{self.prompt_hash[:8]}]",
            "",
            f"### 1. ROLE\n{self.role}",
            "",
            f"### 2. OBJEKTIF\n{self.objective}",
            "",
            "### 3. CONTEXT",
            f"- **Repository Root:** `{self.context.get('repo_root', '.')}`",
            f"- **Target Files:** {', '.join([f'`{f}`' for f in self.context.get('target_files', [])]) or 'None specified'}",
            f"- **Protected Files:** {', '.join([f'`{f}`' for f in self.context.get('protected_files', [])]) or 'None'}",
            "",
            "### 4. RULE",
        ]
        for r in self.rules:
            lines.append(f"- {r}")

        lines.extend([
            "",
            "### 5. REVIEW",
        ])
        for rev in self.review:
            lines.append(f"- {rev}")

        lines.extend([
            "",
            f"### 6. START\n{self.start_step}",
            "",
            "### 7. SHIP",
        ])
        for s in self.ship_criteria:
            lines.append(f"- {s}")

        if self.clarifications:
            lines.extend([
                "",
                "### ⚠️ CLARIFICATIONS REQUIRED",
            ])
            for cl in self.clarifications:
                opts = ", ".join([f"`{o}`" for o in cl.options])
                lines.append(f"- **{cl.element}**: {cl.question} (Options: {opts})")

        return "\n".join(lines)


class PromptSpider:
    """
    Crawls and decomposes user prompts, connects tripartite semantics,
    runs technical flaw detection, and generates 7-Pillar Empirical Blueprints.
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.symbol_map: Optional[SymbolMap] = None
        if os.path.isdir(repo_root):
            try:
                self.symbol_map = RepositoryScanner.scan_directory(repo_root)
            except Exception:
                self.symbol_map = SymbolMap()
        else:
            self.symbol_map = SymbolMap()

        self.bridge = TripartiteSemanticBridge(symbol_map=self.symbol_map)
        self.flaw_detector = TechnicalFlawDetector()

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]

    def _extract_tokens(self, text: str, concept: NormalizedConcept) -> List[SpiderToken]:
        tokens: List[SpiderToken] = []
        text_lower = text.lower()

        # 1. 'claim' extraction: condition, bug, or performance statements
        claim_patterns = [
            (r"\b(fungsi\s+[a-zA-Z0-9_\.-]+\s+lambat)\b", "performance_claim"),
            (r"\b([a-zA-Z0-9_\.-]+\s+(?:rusak|error|gagal|timeout|mati|crash))\b", "defect_claim"),
            (r"\b(tidak\s+jalan|tidak\s+respon|gak\s+respon|broken)\b", "unresponsive_claim"),
        ]
        for pat, norm in claim_patterns:
            for m in re.finditer(pat, text_lower):
                tokens.append(
                    SpiderToken(
                        category="claim",
                        raw_text=m.group(0),
                        normalized_concept=norm,
                        confidence=0.95,
                    )
                )

        # 2. 'file' extraction: explicit file paths or extensions
        file_matches = re.findall(r"[\w/\.-]+\.(?:tsx|jsx|ts|js|py|css|html|json)", text)
        for fm in file_matches:
            tokens.append(
                SpiderToken(
                    category="file",
                    raw_text=fm,
                    normalized_concept="source_file",
                    resolved_entity=fm,
                    confidence=1.0,
                )
            )

        # 3. 'owner' extraction: module or architectural domain
        for fm in file_matches:
            parts = fm.replace("\\", "/").split("/")
            if len(parts) > 1:
                tokens.append(
                    SpiderToken(
                        category="owner",
                        raw_text=parts[0],
                        normalized_concept="domain_owner",
                        resolved_entity=parts[0],
                        confidence=0.9,
                    )
                )

        # Also detect common architectural owners
        for domain in ["canvas", "toolbar", "auth", "session", "database", "spider", "cli"]:
            if domain in text_lower:
                tokens.append(
                    SpiderToken(
                        category="owner",
                        raw_text=domain,
                        normalized_concept=f"{domain}_domain",
                        resolved_entity=domain,
                        confidence=0.85,
                    )
                )

        # 4. 'approval' extraction: high-risk, preservation, or destructive clauses
        approval_patterns = [
            (r"\b(jangan\s+hapus\s+[^\s,]+)\b", "prevent_deletion"),
            (r"\b(jangan\s+ubah\s+[^\s,]+)\b", "prevent_modification"),
            (r"\b(dilarang\s+(?:timpa|hapus|ubah))\b", "forbidden_mutation"),
            (r"\b(hapus\s+[^\s,]+)\b", "destructive_approval"),
            (r"\b(reset\s+[^\s,]+)\b", "state_reset_approval"),
        ]
        for pat, norm in approval_patterns:
            for m in re.finditer(pat, text_lower):
                tokens.append(
                    SpiderToken(
                        category="approval",
                        raw_text=m.group(0),
                        normalized_concept=norm,
                        confidence=0.95,
                    )
                )

        # 5. 'vague' extraction: abstract buzzwords
        vague_phrases = [
            (r"\b(?:buat\s+)?(lebih\s+kenceng)\b", "unspecified_performance"),
            (r"\b(?:buat\s+)?(lebih\s+keren)\b", "aesthetic_ambiguity"),
            (r"\b(rapikan\s+kodenya?)\b", "unscoped_refactoring"),
            (r"\b(?:lebih\s+)?(mantap)\b", "unspecified_quality"),
            (r"\b(?:lebih\s+)?(fleksibel)\b", "unbounded_flexibility"),
        ]
        for pat, norm in vague_phrases:
            for m in re.finditer(pat, text_lower):
                tokens.append(
                    SpiderToken(
                        category="vague",
                        raw_text=m.group(1),
                        normalized_concept=norm,
                        confidence=0.9,
                    )
                )

        return tokens

    def _generate_clarifications(self, tokens: List[SpiderToken]) -> List[ClarificationItem]:
        clarifications: List[ClarificationItem] = []
        for t in tokens:
            if t.category == "vague":
                norm = t.normalized_concept
                if norm == "unspecified_performance":
                    clarifications.append(
                        ClarificationItem(
                            element=t.raw_text,
                            question="Parameter performa apa yang ingin diprioritaskan?",
                            options=["Optimasi Kecepatan Eksekusi (Latency)", "Efisiensi Penggunaan Memori", "Throughput Operasi"],
                        )
                    )
                elif norm in ("unspecified_quality", "aesthetic_ambiguity"):
                    clarifications.append(
                        ClarificationItem(
                            element=t.raw_text,
                            question="Aspek peningkatan apa yang diinginkan secara konkret?",
                            options=["Desain UI HUD Kontekstual & Native CSS", "Arsitektur Kode & Separation of Concerns", "Penambahan Fitur Baru"],
                        )
                    )
                elif norm == "unscoped_refactoring":
                    clarifications.append(
                        ClarificationItem(
                            element=t.raw_text,
                            question="Lingkup perapian kode yang diinginkan?",
                            options=["Pembersihan Dead Code & Linting", "Modularisasi Deep Modules (Ousterhout)", "Ekstraksi Helper Function"],
                        )
                    )
                else:
                    clarifications.append(
                        ClarificationItem(
                            element=t.raw_text,
                            question=f"Mohon berikan rincian konkret untuk '{t.raw_text}':",
                            options=["Sesuai Konvensi Standar Repository", "Batasi pada File Target Saja"],
                        )
                    )
        return clarifications

    def crawl_and_synthesize(self, prompt: str, enforce_contracts: bool = True) -> EmpiricalBlueprint:
        """
        Main pipeline: Crawls prompt, extracts 5 token categories, audits flaws,
        synthesizes 7-Pillar Empirical Blueprint, and binds invariants to memory.
        """
        p_hash = self._compute_hash(prompt)
        concept = self.bridge.normalize_phrase(prompt)
        tokens = self._extract_tokens(prompt, concept)
        clarifications = self._generate_clarifications(tokens)

        # Flaw detection
        prompt_flaws = self.flaw_detector.audit_prompt(prompt, repo_root=self.repo_root)

        # 1. Synthesize ROLE
        action = concept.action
        if action == "design_ui":
            role = "Senior Precision UI & Layout Systems Engineer (Contextual HUD & Native CSS Specialist)"
        elif action == "create_feature":
            role = "Lead Systems Architect & Feature Engineering Specialist"
        elif action == "refactor":
            role = "Principal Software Architect & Modular Refactoring Specialist (Ousterhout's Deep Modules)"
        elif action == "fix_bug":
            role = "Core Systems Reliability Engineer & Defect Resolution Specialist"
        else:
            role = "Autonomous Systems Engineer & Goby Quality Orchestrator"

        # 2. Synthesize OBJEKTIF
        obj_tokens = [t.raw_text for t in tokens if t.category in ("claim", "file", "owner")]
        if obj_tokens:
            objective = f"Eksekusi tugas '{action}' terarah pada target [{', '.join(obj_tokens)}]."
        else:
            objective = f"Eksekusi tugas '{action}' sesuai spesifikasi empiris dan batasan arsitektur repositori."

        # 3. Synthesize CONTEXT
        target_files = [t.resolved_entity for t in tokens if t.category == "file" and t.resolved_entity]
        protected_files = concept.preserved_targets

        context = {
            "repo_root": self.repo_root,
            "target_files": target_files,
            "protected_files": protected_files,
            "action": action,
            "risk_flags": concept.risk_flags,
        }

        # 4. Synthesize RULES
        rules = [
            "Wajib patuhi Single Source of Truth (SSOT); dilarang membuat kontrol ganda / tombol bocor pada komponen berbeda.",
            "Wajib hindari jebakan boxification; gunakan layout CSS elastis tanpa fixed height kaku yang membuat teks tumpah keluar kotak.",
            "Wajib pertahankan arsitektur Deep Modules (MDI >= 1.2); dilarang membuat shallow pass-through wrappers.",
        ]
        if protected_files:
            rules.append(f"MANDATORY PRESERVATION: Dilarang mengubah file yang dilindungi: {', '.join(protected_files)}.")

        for fl in prompt_flaws:
            rules.append(f"FLAW MITIGATION [{fl.severity}]: {fl.suggested_fix}")

        # 5. Synthesize REVIEW
        review = [
            "Seluruh test suite repositori wajib lulus (python -m unittest discover tests/ -> OK).",
            "Goby Gate wajib bersih tanpa unresolved errors (`goby gate` exit code 0).",
            "Verifikasi CCR hard gate dan Scope check pada setiap file yang dimodifikasi.",
        ]
        if target_files:
            review.append(f"Jalankan `goby check` pada file target: {', '.join(target_files)}.")

        # 6. Synthesize START
        if target_files:
            start_step = f"Jalankan `view_file` pada target utama `{target_files[0]}` untuk memeriksa ground truth state sebelum menulis kode."
        else:
            start_step = "Jalankan eksplorasi direktori atau `goby map` untuk mengidentifikasi file ground truth."

        # 7. Synthesize SHIP
        ship_criteria = [
            "Zero CCR gate violations.",
            "All unit tests pass cleanly.",
            "Goby Gate exit code 0.",
            "Session context saved to conversation memory (`goby save`).",
        ]

        # Mechanical Contract & Obligation Binding: Register to cognitive_map.json if requested
        if enforce_contracts:
            try:
                from core.state_memory import StateMemoryManager
                mem_path = os.path.join(self.repo_root, "cognitive_map.json")
                memory = StateMemoryManager(mem_path)

                # 1. Register claims as formal task obligations
                claim_tokens = [t.raw_text for t in tokens if t.category == "claim"]
                if not claim_tokens and prompt.strip():
                    claim_tokens = [prompt.strip()]

                for c in claim_tokens:
                    memory.record_obligation(
                        claim=c,
                        source="prompt_spider",
                        target_files=target_files,
                        required_authority="dynamic_test",
                    )

                # 2. Record protected files blueprint if present
                if protected_files and hasattr(memory, "record_spider_blueprint"):
                    memory.record_spider_blueprint(p_hash, {
                        "prompt": prompt,
                        "protected_files": protected_files,
                        "target_files": target_files,
                    })
            except Exception:
                pass

        return EmpiricalBlueprint(
            role=role,
            objective=objective,
            context=context,
            rules=rules,
            review=review,
            start_step=start_step,
            ship_criteria=ship_criteria,
            tokens=tokens,
            clarifications=clarifications,
            detected_flaws=prompt_flaws,
            prompt_hash=p_hash,
        )
