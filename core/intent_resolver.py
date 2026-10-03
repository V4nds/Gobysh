"""
Intent Resolver for Goby Framework v5.0.
Translates ambiguous/abstract user requests into structured intent trees.
Uses keyword heuristics (pure Python, no LLM dependency) with bilingual support.

This module is the FIRST step in the Goby pipeline:
  User Request → IntentResolver → IntentTree → Agent Action

When confidence is below threshold, it auto-generates clarification questions
so the agent asks BEFORE writing code — not after failing.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.semantics.specification import Requirement, SemanticSpecification, DialecticalContract
from core.semantics.constraints import ConstraintModel
from core.semantics.intermediate_representation import SemanticEntity, SemanticIR
from core.semantics.preservation import PreservationContract
from core.semantics.scope import ScopeNormalizer
from core.semantics.negation import NegationHandler
from core.semantics.contract_validator import ContractValidator
from core.semantics.dependency_graph import DependencyGraph
from core.translation.scanner import RepositoryScanner
from core.translation.engine import CodeSemanticMapper, MappingReport


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class IntentNode:
    """A single resolved intent from user input."""
    task_type: str          # fix_bug, create_feature, refactor, design_ui, explain, test, configure, deploy
    confidence: float       # 0.0 - 1.0
    description: str        # Human-readable summary of what the agent should do
    target_files: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticContract:
    """Explicit semantic contract extracted from prompt constraints."""
    forbidden_targets: List[str] = field(default_factory=list)
    preserve_existing: bool = False
    strict_scope: List[str] = field(default_factory=list)
    expected_traits: List[str] = field(default_factory=list)
    action_verb: str = ""
    contradictions: List[str] = field(default_factory=list)
    semantic_ir_dict: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forbidden_targets": self.forbidden_targets,
            "preserve_existing": self.preserve_existing,
            "strict_scope": self.strict_scope,
            "expected_traits": self.expected_traits,
            "action_verb": self.action_verb,
            "contradictions": self.contradictions,
        }


@dataclass
class IntentTree:
    """Complete parsed intent from a user request."""
    raw_input: str
    primary_intent: IntentNode
    secondary_intents: List[IntentNode] = field(default_factory=list)
    clarification_needed: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    detected_language: str = "unknown"  # "id" (Indonesian), "en" (English), "mixed"
    ambiguity_score: float = 0.0        # 0.0 = crystal clear, 1.0 = completely ambiguous
    semantic_contract: SemanticContract = field(default_factory=SemanticContract)
    semantic_ir: Optional[SemanticIR] = None
    code_mapping: Optional[MappingReport] = None
    dialectical_contract: Optional[DialecticalContract] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_input": self.raw_input,
            "primary_intent": {
                "task_type": self.primary_intent.task_type,
                "confidence": self.primary_intent.confidence,
                "description": self.primary_intent.description,
                "target_files": self.primary_intent.target_files,
                "constraints": self.primary_intent.constraints,
            },
            "secondary_intents": [
                {
                    "task_type": si.task_type,
                    "confidence": si.confidence,
                    "description": si.description,
                }
                for si in self.secondary_intents
            ],
            "clarification_needed": self.clarification_needed,
            "clarification_questions": self.clarification_questions,
            "detected_language": self.detected_language,
            "ambiguity_score": round(self.ambiguity_score, 2),
            "semantic_contract": self.semantic_contract.to_dict(),
            "semantic_ir": self.semantic_ir.to_dict() if self.semantic_ir else None,
            "code_mapping": self.code_mapping.to_dict() if self.code_mapping else None,
            "dialectical_contract": self.dialectical_contract.to_dict() if self.dialectical_contract else None,
        }





# ---------------------------------------------------------------------------
# Keyword Pattern Database (Bilingual: Indonesian + English)
# ---------------------------------------------------------------------------

# Each entry: (task_type, weight, [keywords])
_INTENT_PATTERNS: List[Tuple[str, float, List[str]]] = [
    # Bug fixing
    ("fix_bug", 0.9, [
        "error", "bug", "fix", "broken", "crash", "gagal", "rusak", "perbaiki",
        "tidak jalan", "not working", "doesn't work", "failed", "traceback",
        "exception", "undefined", "null", "nan", "salah", "wrong", "mati",
        "kenapa", "why", "issue", "problem", "masalah",
    ]),
    # Create/add feature
    ("create_feature", 0.85, [
        "buat", "bikin", "create", "add", "tambah", "implement", "build",
        "new", "baru", "feature", "fitur", "fungsi", "function", "module",
        "page", "halaman", "component", "komponen", "endpoint", "api",
        "generate", "develop", "bangun",
    ]),
    # Refactor
    ("refactor", 0.8, [
        "refactor", "clean", "optimize", "improve", "rapikan", "perbaiki struktur",
        "simplify", "sederhanakan", "modular", "reorganize", "restructure",
        "efisien", "efficient", "performance", "speed", "cepat",
    ]),
    # UI/UX Design
    ("design_ui", 0.85, [
        "design", "desain", "ui", "ux", "layout", "tampilan", "style", "css",
        "responsive", "animasi", "animation", "warna", "color", "theme",
        "dark mode", "light mode", "beautiful", "cantik", "bagus", "keren",
        "modern", "glassmorphism", "gradient", "hover", "transition",
        "font", "typography", "spacing", "margin", "padding",
    ]),
    # Explain/understand
    ("explain", 0.75, [
        "explain", "jelaskan", "apa itu", "what is", "how does", "bagaimana",
        "kenapa", "why", "understand", "pahami", "arti", "meaning",
        "dokumentasi", "documentation", "cara kerja", "how it works",
    ]),
    # Testing
    ("test", 0.85, [
        "test", "testing", "unittest", "pytest", "jest", "spec", "assert",
        "coverage", "mock", "spy", "fixture", "tes", "uji", "validasi",
        "verify", "check", "periksa",
    ]),
    # Configuration/setup
    ("configure", 0.7, [
        "config", "konfigurasi", "setup", "install", "setting", "env",
        "environment", "deploy", "docker", "package", "dependency",
        "requirement", "pip", "npm", "yarn",
    ]),
    # Delete/remove
    ("delete", 0.8, [
        "hapus", "delete", "remove", "buang", "hilangkan", "drop",
        "uninstall", "clean up", "bersihkan",
    ]),
]

# File extension patterns for auto-detecting target files
_FILE_PATTERNS = re.compile(
    r'[\w/\\.-]+\.(?:py|js|jsx|ts|tsx|kt|kts|css|html|json|yaml|yml|toml|md|sql)\b',
    re.IGNORECASE,
)

# Ambiguity indicators
_AMBIGUITY_MARKERS_ID = [
    "mungkin", "kayaknya", "sepertinya", "entah", "gak tau", "ga tau",
    "bingung", "gimana ya", "kira-kira", "terserah", "pokoknya",
    "yang bagus", "yang keren", "sesuatu", "something",
]

_AMBIGUITY_MARKERS_EN = [
    "maybe", "perhaps", "somehow", "whatever", "something like",
    "not sure", "i think", "i guess", "kind of", "sort of",
    "idk", "dunno",
]

# Language detection
_INDONESIAN_MARKERS = [
    "aku", "saya", "tolong", "buat", "bikin", "tambah", "tambahkan", "fitur", "baru", "hapus", "perbaiki", "kalibrasi", "cek", "jalankan", "simpan", "kembali",
    "gimana", "kenapa", "apa", "ini", "itu", "yang", "dan", "atau",
    "jadi", "sudah", "belum", "mau", "ingin", "coba", "dong", "deh",
    "nih", "lah", "kan", "aja", "banget", "sekali",
]


# ---------------------------------------------------------------------------
# Intent Resolver Engine
# ---------------------------------------------------------------------------

class IntentResolver:
    """
    Parses raw user input into a structured IntentTree.
    Uses keyword matching with confidence scoring — no LLM needed.

    Usage:
        resolver = IntentResolver()
        intent = resolver.resolve("tolong perbaiki error di app.js")
        if intent.clarification_needed:
            # Ask user the clarification_questions
            ...
        else:
            # Proceed with intent.primary_intent.task_type
            ...
    """

    CONFIDENCE_THRESHOLD = 0.4  # Below this → ask for clarification
    AMBIGUITY_THRESHOLD = 0.5   # Above this → flag as ambiguous

    def resolve(self, user_input: str, repo_root: Optional[str] = None) -> IntentTree:
        """
        Main entry point. Resolves raw user text into an IntentTree.
        """
        if not user_input or not user_input.strip():
            return IntentTree(
                raw_input=user_input or "",
                primary_intent=IntentNode(
                    task_type="unknown",
                    confidence=0.0,
                    description="Empty or blank input received.",
                ),
                clarification_needed=True,
                clarification_questions=["Apa yang ingin kamu kerjakan? / What would you like to do?"],
                ambiguity_score=1.0,
            )

        text = user_input.strip()
        text_lower = text.lower()

        # Step 1: Detect language
        detected_lang = self._detect_language(text_lower)

        # Step 2: Extract file references
        target_files = _FILE_PATTERNS.findall(text)

        # Step 3: Score each intent pattern
        scored_intents = self._score_intents(text_lower)

        # Step 4: Calculate ambiguity
        ambiguity = self._calculate_ambiguity(text_lower, scored_intents)

        # Step 5: Build primary and secondary intents
        if not scored_intents:
            primary = IntentNode(
                task_type="unknown",
                confidence=0.0,
                description=f"Could not determine intent from: {text[:100]}",
                target_files=target_files,
            )
            secondary = []
        else:
            best = scored_intents[0]
            primary = IntentNode(
                task_type=best[0],
                confidence=best[1],
                description=self._generate_description(best[0], text, detected_lang),
                target_files=target_files,
                constraints=self._extract_constraints(text_lower, best[0]),
            )
            secondary = [
                IntentNode(
                    task_type=s[0],
                    confidence=s[1],
                    description=self._generate_description(s[0], text, detected_lang),
                )
                for s in scored_intents[1:3]  # Max 2 secondary intents
                if s[1] >= 0.3
            ]

        # Step 6: Extract semantic contract & build formal ConstraintModel
        semantic_contract = self._extract_semantic_contract(text, text_lower, primary.task_type)

        constraint_model = ConstraintModel(
            forbidden_targets=semantic_contract.forbidden_targets,
            preserve_existing=semantic_contract.preserve_existing,
            strict_scope=semantic_contract.strict_scope,
        )

        # Detect contradictions between constraints and target files/action
        contradictions = constraint_model.detect_contradictions(
            target_files=primary.target_files,
            action=primary.task_type,
        )
        semantic_contract.contradictions = contradictions

        # Build formal SemanticSpecification
        spec_reqs = []
        if primary.task_type != "unknown":
            spec_reqs.append(
                Requirement(
                    id="REQ-001",
                    description=primary.description,
                    source_text=text,
                    action=primary.task_type,
                    target_entities=primary.target_files,
                    status="UNMAPPED",
                )
            )

        # Step 6.5: Dialectical evaluation (Anti-Sycophancy)
        dialectical_contract = self._evaluate_dialectical_sparring(
            text=text,
            text_lower=text_lower,
            primary=primary,
            lang=detected_lang,
        )

        spec = SemanticSpecification(
            id=f"SPEC-{abs(hash(text)) % 1000000:06d}",
            language=detected_lang,
            raw_prompt=text,
            requirements=spec_reqs,
            dialectical_contract=dialectical_contract,
        )

        entities = [
            SemanticEntity(name=tf, entity_type="file") for tf in primary.target_files
        ]

        # Build first-class PreservationContract
        preservation_contract = PreservationContract(
            required=semantic_contract.preserve_existing,
            invariants=["preserve_existing_system"] if semantic_contract.preserve_existing else [],
            verification_strategy=["existing_test_suite", "ast_signature_check"] if semantic_contract.preserve_existing else [],
        )

        semantic_ir = SemanticIR(
            specification=spec,
            intent={
                "action": primary.task_type,
                "target": ", ".join(primary.target_files) if primary.target_files else primary.task_type,
                "description": primary.description,
            },
            entities=entities,
            constraints=constraint_model,
            preservation=preservation_contract,
            contradictions=contradictions,
        )
        semantic_contract.semantic_ir_dict = semantic_ir.to_dict()

        # Step 7: Validate contract through ContractValidator
        validator = ContractValidator()
        val_result = validator.validate(semantic_ir)

        for err in val_result.errors:
            if err not in contradictions:
                contradictions.append(err)
        semantic_contract.contradictions = contradictions

        # Step 7.5: Code mapping if repo_root is provided
        code_mapping = None
        if repo_root:
            try:
                sym_map = RepositoryScanner.scan_directory(repo_root)
                dg = DependencyGraph.build_from_symbol_map(sym_map)
                mapper = CodeSemanticMapper(sym_map, dg)
                code_mapping = mapper.map_intent(
                    entities=semantic_ir.entities,
                    requirements=semantic_ir.specification.requirements,
                    protected_symbols=semantic_ir.protected_symbols,
                )
                if code_mapping.target_files:
                    for tf in code_mapping.target_files:
                        if tf not in primary.target_files:
                            primary.target_files.append(tf)

                if code_mapping.protected_symbols_violated:
                    prot_err = f"Modifications touch protected symbol(s): {', '.join(code_mapping.protected_symbols_violated)}"
                    if prot_err not in contradictions:
                        contradictions.append(prot_err)
                    semantic_contract.contradictions = contradictions
            except Exception:
                pass

        # Step 8: Determine if clarification is needed
        needs_clarification = (
            primary.confidence < self.CONFIDENCE_THRESHOLD
            or ambiguity > self.AMBIGUITY_THRESHOLD
            or not val_result.valid
            or (code_mapping is not None and bool(code_mapping.protected_symbols_violated))
        )

        clarification_qs = []
        if needs_clarification:
            clarification_qs = self._generate_clarifications(
                text, primary.task_type, detected_lang, ambiguity
            )

        # If contradictions exist, prepend high-priority clarification question and bump ambiguity
        if contradictions:
            clarification_qs.insert(0, f"[CONTRADICTION DETECTED] {contradictions[0]} Please clarify.")
            ambiguity = max(ambiguity, 0.85)

        return IntentTree(
            raw_input=text,
            primary_intent=primary,
            secondary_intents=secondary,
            clarification_needed=needs_clarification,
            clarification_questions=clarification_qs,
            detected_language=detected_lang,
            ambiguity_score=ambiguity,
            semantic_contract=semantic_contract,
            semantic_ir=semantic_ir,
            code_mapping=code_mapping,
            dialectical_contract=dialectical_contract,
        )

    # -------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------

    def _detect_language(self, text_lower: str) -> str:
        """Detect whether input is Indonesian, English, or mixed."""
        words = set(re.findall(r'\b\w+\b', text_lower))
        id_hits = sum(1 for m in _INDONESIAN_MARKERS if m in words)
        total_words = len(words) if words else 1

        id_ratio = id_hits / total_words if total_words > 0 else 0

        if id_ratio > 0.15:
            return "id"
        elif id_ratio > 0.05:
            return "mixed"
        return "en"

    def _score_intents(self, text_lower: str) -> List[Tuple[str, float]]:
        """Score each intent pattern against the input text. Returns sorted list."""
        results = []
        words = set(re.findall(r'\b\w+\b', text_lower))

        for task_type, base_weight, keywords in _INTENT_PATTERNS:
            hits = 0
            for kw in keywords:
                if " " in kw:
                    # Multi-word keyword: check as substring
                    if kw in text_lower:
                        hits += 1.5  # Multi-word matches are stronger signals
                else:
                    if kw in words:
                        hits += 1.0

            if hits > 0:
                # Normalize: more keyword hits → higher confidence, capped at base_weight
                keyword_density = min(hits / 3.0, 1.0)  # 3 hits = max density
                confidence = round(base_weight * keyword_density, 3)
                results.append((task_type, confidence))

        # Sort by confidence descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _calculate_ambiguity(
        self, text_lower: str, scored_intents: List[Tuple[str, float]]
    ) -> float:
        """
        Calculate ambiguity score based on:
        1. Presence of ambiguity markers
        2. Competing intents with similar scores
        3. Input length (very short = more ambiguous)
        """
        score = 0.0

        # Factor 1: Ambiguity markers
        all_markers = _AMBIGUITY_MARKERS_ID + _AMBIGUITY_MARKERS_EN
        marker_hits = sum(1 for m in all_markers if m in text_lower)
        score += min(marker_hits * 0.15, 0.45)

        # Factor 2: Competing intents
        if len(scored_intents) >= 2:
            top_conf = scored_intents[0][1]
            second_conf = scored_intents[1][1]
            if top_conf > 0 and second_conf / top_conf > 0.8:
                # Two intents are very close → ambiguous
                score += 0.25

        # Factor 3: Input length
        word_count = len(text_lower.split())
        if word_count <= 3:
            score += 0.2
        elif word_count <= 6:
            score += 0.1

        # Factor 4: No intents matched at all
        if not scored_intents:
            score += 0.4

        return min(score, 1.0)

    def _generate_description(self, task_type: str, raw_text: str, lang: str) -> str:
        """Generate a human-readable description of the detected intent."""
        descriptions = {
            "fix_bug": {
                "id": f"Perbaiki bug/error yang disebutkan dalam request user.",
                "en": f"Fix the bug/error described in the user's request.",
            },
            "create_feature": {
                "id": f"Buat fitur/komponen baru sesuai permintaan user.",
                "en": f"Create a new feature/component as requested.",
            },
            "refactor": {
                "id": f"Refactor dan optimasi kode yang disebutkan.",
                "en": f"Refactor and optimize the mentioned code.",
            },
            "design_ui": {
                "id": f"Desain/perbaiki UI/UX sesuai standar modern.",
                "en": f"Design/improve UI/UX to modern standards.",
            },
            "explain": {
                "id": f"Jelaskan konsep/kode yang ditanyakan user.",
                "en": f"Explain the concept/code the user asked about.",
            },
            "test": {
                "id": f"Tulis atau jalankan test untuk kode yang dimaksud.",
                "en": f"Write or run tests for the specified code.",
            },
            "configure": {
                "id": f"Konfigurasi/setup environment atau dependencies.",
                "en": f"Configure/setup environment or dependencies.",
            },
            "delete": {
                "id": f"Hapus/bersihkan kode atau file yang dimaksud.",
                "en": f"Delete/clean up the specified code or files.",
            },
            "unknown": {
                "id": f"Intent tidak terdeteksi. Perlu klarifikasi.",
                "en": f"Intent not detected. Clarification needed.",
            },
        }

        lang_key = "id" if lang in ("id", "mixed") else "en"
        return descriptions.get(task_type, descriptions["unknown"]).get(lang_key, "")

    def _extract_constraints(self, text_lower: str, task_type: str) -> Dict[str, Any]:
        """Extract specific constraints from user text."""
        constraints: Dict[str, Any] = {}

        # Performance constraints
        if any(w in text_lower for w in ["cepat", "fast", "performance", "speed", "optimize"]):
            constraints["performance_sensitive"] = True

        # Compatibility constraints
        if any(w in text_lower for w in ["backward", "compatible", "legacy", "lama", "versi lama"]):
            constraints["backward_compatible"] = True

        # No-breaking-change constraint
        if any(w in text_lower for w in [
            "jangan ubah", "don't change", "don't break", "jangan rusak",
            "keep existing", "tetap", "preserve",
        ]):
            constraints["no_breaking_changes"] = True

        # Technology constraints
        for tech in ["react", "vue", "angular", "next", "vite", "django", "flask", "fastapi"]:
            if tech in text_lower:
                constraints["technology"] = tech
                break

        return constraints

    def _extract_semantic_contract(
        self, text: str, text_lower: str, task_type: str
    ) -> SemanticContract:
        """Extract explicit semantic contract and constraints from Indonesian & English text."""
        # Advanced bilingual negation extraction
        neg_res = NegationHandler.parse_negations(text)
        forbidden_targets = list(neg_res.forbidden_targets)

        # Fallback keyword regex
        neg_patterns = [
            r'(?:jangan|don\'?t|tidak boleh|tanpa|without)\s+(?:ubah|ganti|edit|sentuh|change|touch|modify|menghapus|remove|delete)\s+(?:file\s+)?([a-zA-Z0-9_./\-]+)',
            r'(?:jangan|don\'?t|without)\s+(?:sentuh|touch)\s+([a-zA-Z0-9_./\-]+)',
        ]
        for pat in neg_patterns:
            for match in re.finditer(pat, text_lower):
                target = match.group(1).strip()
                if target and target not in forbidden_targets and target not in ("file", "table", "tabel", "fungsi", "method", "ini"):
                    forbidden_targets.append(target)

        # Preservation constraint
        preserve_existing = neg_res.preserve_demanded or any(p in text_lower for p in [
            "tanpa menghapus", "tanpa merusak", "tanpa ubah method lama",
            "tanpa menghapus method", "tanpa menghapus fungsi", "preserve",
            "keep existing", "jangan hapus", "don't delete", "don't remove"
        ])

        # Strict scope constraint: hanya file X / only in file X
        strict_scope = []
        scope_matches = re.finditer(r'(?:hanya\s+(?:di|pada|untuk)?|only\s+(?:in|on)?)\s+([a-zA-Z0-9_./\-]+)', text_lower)
        for sm in scope_matches:
            s_target = sm.group(1).strip()
            if s_target and s_target not in ("file", "fungsi", "method", "ini"):
                norm_scope = ScopeNormalizer.normalize_path(s_target)
                if norm_scope and norm_scope not in strict_scope:
                    strict_scope.append(norm_scope)

        # Expected traits
        expected_traits = []
        trait_keywords = {
            "validation": ["validasi", "pengecekan", "cek", "validate", "check", "assert"],
            "auth": ["autentikasi", "auth", "login", "token", "jwt", "password"],
            "refactor": ["refactor", "rapikan", "restrukturisasi", "clean up", "tidying"],
            "security": ["keamanan", "aman", "sanitize", "security", "protect"],
            "testing": ["test", "uji", "unit test", "pengujian"],
            "documentation": ["dokumentasi", "docstring", "komentar", "docs"],
        }
        for trait, kw_list in trait_keywords.items():
            if any(kw in text_lower for kw in kw_list):
                expected_traits.append(trait)

        return SemanticContract(
            forbidden_targets=forbidden_targets,
            preserve_existing=preserve_existing,
            strict_scope=strict_scope,
            expected_traits=expected_traits,
            action_verb=task_type,
        )

    def _generate_clarifications(
        self, raw_text: str, task_type: str, lang: str, ambiguity: float
    ) -> List[str]:
        """Generate clarification questions based on what's missing."""
        questions = []
        is_id = lang in ("id", "mixed")

        if task_type == "unknown" or ambiguity > 0.7:
            questions.append(
                "Bisa jelaskan lebih detail apa yang ingin kamu lakukan?"
                if is_id else
                "Could you describe in more detail what you'd like to do?"
            )

        if task_type == "fix_bug":
            questions.append(
                "Bisa kirimkan error message atau traceback yang muncul?"
                if is_id else
                "Could you share the error message or traceback?"
            )

        if task_type == "create_feature":
            questions.append(
                "Fitur ini akan ditambahkan di file mana, atau ini fitur yang benar-benar baru?"
                if is_id else
                "Which file should this feature be added to, or is it entirely new?"
            )

        if task_type == "design_ui":
            questions.append(
                "Apakah ada referensi desain atau contoh tampilan yang diinginkan?"
                if is_id else
                "Do you have any design references or examples in mind?"
            )

        # General: always ask about scope if ambiguous
        if ambiguity > 0.5 and len(questions) < 3:
            questions.append(
                "Apakah perubahan ini harus terbatas pada file tertentu saja?"
                if is_id else
                "Should this change be limited to specific files?"
            )

        return questions[:3]  # Max 3 questions

    def _evaluate_dialectical_sparring(
        self, text: str, text_lower: str, primary: IntentNode, lang: str
    ) -> DialecticalContract:
        """
        Anti-Sycophancy & Dialectical Sparring Engine.
        Critically evaluates planning/architecture intents to prevent premature agreement,
        blindspot omissions, and deterministic boilerplate traps.
        """
        is_id = lang in ("id", "mixed")
        naive_assumptions: List[str] = []
        tradeoffs: List[str] = []
        counter_vector: str = ""
        anti_template = False
        is_sycophantic = False

        task = primary.task_type
        if task in ("create_feature", "design_ui", "refactor"):
            # Check for sycophancy risk: blindly executing without considering trade-offs
            if not any(w in text_lower for w in ["tradeoff", "risiko", "risk", "alternatif", "alternative", "evaluasi"]):
                is_sycophantic = True
                naive_assumptions.append(
                    "Diasumsikan pendekatan yang diminta langsung dieksekusi tanpa menguji kompromi arsitektural atau blindspots."
                    if is_id else
                    "Assumes requested approach is immediately executed without stress-testing architectural trade-offs or blindspots."
                )

            # UI-specific anti-boxification & anti-template checks
            if task == "design_ui":
                anti_template = True
                tradeoffs.append(
                    "Risiko over-encapsulation (boxification) di mana teks dan simbol dipaksa masuk ke card containers klise."
                    if is_id else
                    "Risk of over-encapsulation (boxification) where symbols/text are forced into generic card containers."
                )
                counter_vector = (
                    "Gunakan integrasi HUD kontekstual, arsitektur slot terarah, atau layout CSS native daripada membungkus semua nilai dalam box/card."
                    if is_id else
                    "Use contextual inline HUDs, slot-based layouts, or native CSS rather than wrapping every value into cards."
                )
            elif task == "create_feature":
                tradeoffs.append(
                    "Risiko duplikasi fitur (double fitur bocor) pada komponen atau permukaan layout yang berbeda."
                    if is_id else
                    "Risk of feature duplication (leaked redundant controls) across disparate layout components."
                )
                counter_vector = (
                    "Verifikasi ComponentCapabilityRegistry sebelum membuat kontrol baru untuk memastikan Single Source of Truth."
                    if is_id else
                    "Verify ComponentCapabilityRegistry before mounting new controls to ensure Single Source of Truth."
                )
            elif task == "refactor":
                tradeoffs.append(
                    "Risiko regresi fungsional atau breaking changes tersembunyi pada consumer API lama."
                    if is_id else
                    "Risk of hidden functional regressions or API contract breaking changes on existing consumers."
                )
                counter_vector = (
                    "Terapkan PreservationContract ketat dan verifikasi AST signature sebelum refactoring."
                    if is_id else
                    "Enforce strict PreservationContract and AST signature verification prior to refactoring."
                )

        return DialecticalContract(
            naive_assumptions=naive_assumptions,
            tradeoffs_identified=tradeoffs,
            counter_vector=counter_vector,
            anti_template_flag=anti_template,
            is_sycophantic=is_sycophantic,
        )

