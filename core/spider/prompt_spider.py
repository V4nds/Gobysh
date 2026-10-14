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
    visual_diagram: Optional[str] = None

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
            "visual_diagram": self.visual_diagram,
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

        if self.visual_diagram:
            lines.extend([
                "",
                "### 8. VISUAL ARCHITECTURE SCHEMATIC (diagram-design standard)",
                self.visual_diagram,
            ])

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

        # 6. 'exemplar' extraction: illustrative samples that should NOT be parroted verbatim
        exemplar_pattern = r"\b(?:misal(?:kan)?|contoh(?:nya)?|seperti|kayak|ibarat(?:nya)?|for example|for instance|e\.g\.,?|such as)\s+([^.;\n]+)"
        for m in re.finditer(exemplar_pattern, text_lower):
            raw_clause = m.group(1).strip()
            # Split items separated by comma, 'atau', 'dan', 'or', 'and'
            parts = re.split(r",\s*|\s+(?:atau|dan|or|and)\s+", raw_clause)
            for part in parts:
                clean_part = part.strip().strip("'\"")
                if clean_part and len(clean_part) > 1 and clean_part not in ("dll", "etc", "dsb"):
                    tokens.append(
                        SpiderToken(
                            category="exemplar",
                            raw_text=clean_part,
                            normalized_concept="illustrative_exemplar",
                            confidence=0.95,
                        )
                    )

        # 7. 'reference' extraction: external URLs, repositories, and learning references
        # 7a. Direct URLs
        url_matches = re.findall(r"https?://[^\s,;'\"]+", text)
        for url in url_matches:
            tokens.append(
                SpiderToken(
                    category="reference",
                    raw_text=url,
                    normalized_concept="external_reference_url",
                    resolved_entity=url,
                    confidence=1.0,
                )
            )

        # 7b. GitHub repository shorthand (e.g. repo user/repo or github.com/user/repo)
        repo_matches = re.findall(r"\b(?:repo|repository)\s+([a-zA-Z0-9_\.-]+/[a-zA-Z0-9_\.-]+)\b", text_lower)
        for rm in repo_matches:
            tokens.append(
                SpiderToken(
                    category="reference",
                    raw_text=rm,
                    normalized_concept="external_repository",
                    resolved_entity=rm,
                    confidence=0.95,
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

    def generate_editorial_diagram(self, prompt: str, blueprint: EmpiricalBlueprint) -> str:
        """
        Synthesizes a self-contained HTML/SVG architectural diagram following
        Cathryn Lavery's diagram-design editorial standards (4/10 density, 1px hairlines, 1 focal accent).
        """
        req_text = (prompt[:36] + "...") if len(prompt) > 36 else prompt
        if not req_text:
            req_text = "User Intent"

        target_files = blueprint.context.get("target_files", [])
        target_display = target_files[0] if target_files else "Workspace AST"
        if len(target_display) > 24:
            target_display = os.path.basename(target_display)

        p_hash = blueprint.prompt_hash[:8]

        return f'''<!-- GOBY EDITORIAL DIAGRAM (diagram-design standard: 4/10 density, 1px hairline, 1 focal accent) -->
<div class="goby-diagram-editorial" style="background:#f5f5f5; border:1px solid #d4d4d4; border-radius:6px; padding:20px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color:#2d3142; max-width:880px; margin:16px 0;">
  <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e0e0e0; padding-bottom:10px; margin-bottom:16px;">
    <div>
      <span style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em; color:#777; font-weight:600;">System Schematic &bull; Type Architecture</span>
      <h4 style="margin:4px 0 0 0; font-size:15px; font-weight:600; color:#2d3142;">Prompt Execution Blueprint [{p_hash}]</h4>
    </div>
    <div style="font-size:11px; color:#555; background:#fff; border:1px solid #e0e0e0; border-radius:4px; padding:3px 8px;">Density: 4/10</div>
  </div>
  <svg viewBox="0 0 820 160" width="100%" height="160" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow:visible;">
    <!-- Node 1: User Prompt -->
    <g transform="translate(10, 35)">
      <rect x="0" y="0" width="170" height="70" rx="4" fill="#ffffff" stroke="#2d3142" stroke-width="1" />
      <text x="14" y="24" font-size="10" font-weight="700" fill="#777" letter-spacing="0.05em">INPUT CLAIM</text>
      <text x="14" y="46" font-size="12" font-weight="500" fill="#2d3142">{req_text}</text>
    </g>

    <!-- Connector 1 -> 2 -->
    <path d="M 180 70 L 230 70" fill="none" stroke="#2d3142" stroke-width="1" />
    <polygon points="230,70 224,66 224,74" fill="#2d3142" />

    <!-- Node 2: Prompt Spider & CCR (FOCAL ACCENT: Coral #bf4520) -->
    <g transform="translate(230, 25)">
      <rect x="0" y="0" width="180" height="90" rx="4" fill="#ffffff" stroke="#bf4520" stroke-width="1" />
      <rect x="0" y="0" width="180" height="4" fill="#bf4520" />
      <text x="14" y="24" font-size="10" font-weight="700" fill="#bf4520" letter-spacing="0.05em">ORCHESTRATOR [FOCAL]</text>
      <text x="14" y="46" font-size="13" font-weight="600" fill="#2d3142">Prompt Spider &amp; CCR</text>
      <text x="14" y="66" font-size="11" fill="#666">7-Pillar Contract Binding</text>
    </g>

    <!-- Connector 2 -> 3 -->
    <path d="M 410 70 L 460 70" fill="none" stroke="#2d3142" stroke-width="1" />
    <polygon points="460,70 454,66 454,74" fill="#2d3142" />

    <!-- Node 3: Ground Truth Target -->
    <g transform="translate(460, 35)">
      <rect x="0" y="0" width="170" height="70" rx="4" fill="#ffffff" stroke="#2d3142" stroke-width="1" />
      <text x="14" y="24" font-size="10" font-weight="700" fill="#777" letter-spacing="0.05em">TARGET ARTIFACT</text>
      <text x="14" y="46" font-size="12" font-weight="500" fill="#2d3142">{target_display}</text>
    </g>

    <!-- Connector 3 -> 4 -->
    <path d="M 630 70 L 670 70" fill="none" stroke="#2d3142" stroke-width="1" />
    <polygon points="670,70 664,66 664,74" fill="#2d3142" />

    <!-- Node 4: Dynamic Test & Exit Gate -->
    <g transform="translate(670, 35)">
      <rect x="0" y="0" width="140" height="70" rx="4" fill="#ffffff" stroke="#2d3142" stroke-width="1" />
      <text x="12" y="24" font-size="10" font-weight="700" fill="#777" letter-spacing="0.05em">EXIT GATE (3P)</text>
      <text x="12" y="46" font-size="12" font-weight="600" fill="#2d3142">goby audit</text>
      <text x="12" y="60" font-size="10" fill="#888">SHA-256 Provenance</text>
    </g>
  </svg>
</div>'''

    def crawl_and_synthesize(
        self,
        prompt: str,
        enforce_contracts: bool = True,
        generate_visual: bool = False
    ) -> EmpiricalBlueprint:
        """
        Main pipeline: Crawls prompt, extracts 5 token categories, audits flaws,
        synthesizes 7-Pillar Empirical Blueprint, optionally generates visual diagram,
        and binds invariants to memory.
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

        # Exemplar Induction & Anti-Parroting Synthesis
        exemplar_tokens = [t.raw_text for t in tokens if t.category == "exemplar"]
        if exemplar_tokens:
            from core.spider.exemplar_generalizer import ExemplarGeneralizer
            generalizer = ExemplarGeneralizer()
            induction_res = generalizer.induce_and_expand(exemplar_tokens)
            if induction_res.guardrail_rule:
                rules.append(induction_res.guardrail_rule)
            context["exemplar_domain"] = induction_res.inferred_domain
            context["exemplar_variations"] = induction_res.variations

        # Reference Synthesis & Identity Preservation
        reference_tokens = [t.raw_text for t in tokens if t.category == "reference"]
        if reference_tokens:
            from core.semantics.project_anchor import ProjectIdentityAnchor
            anchor = ProjectIdentityAnchor(self.repo_root)
            for ref in reference_tokens:
                ref_synth = anchor.synthesize_reference(ref)
                if ref_synth.guardrail_rule:
                    rules.append(ref_synth.guardrail_rule)
            context["external_references"] = reference_tokens

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

        blueprint = EmpiricalBlueprint(
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

        if generate_visual:
            blueprint.visual_diagram = self.generate_editorial_diagram(prompt, blueprint)

        return blueprint
