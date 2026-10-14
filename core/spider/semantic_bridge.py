"""
Tripartite Semantic Bridge for Goby v5.3.
Provides high-fidelity, bidirectional alignment across:
  1. Natural Language (Indonesian / English / Mixed Slang)
  2. Semantic Concept & Intent Ontologies
  3. Ground-Truth Programming Language AST (Symbols & Files)
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set

from core.translation.symbol_mapper import SymbolMap, Symbol


@dataclass
class NormalizedConcept:
    """Represents a normalized semantic concept parsed from natural language."""
    action: str = "unknown"
    keywords: List[str] = field(default_factory=list)
    has_preservation: bool = False
    preserved_targets: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "keywords": self.keywords,
            "has_preservation": self.has_preservation,
            "preserved_targets": self.preserved_targets,
            "risk_flags": self.risk_flags,
            "raw_text": self.raw_text,
        }


@dataclass
class ResolvedASTEntity:
    """Represents an AST symbol or source file grounded in the repository."""
    symbol_name: str
    file_path: str
    kind: str = "file"  # file | class | function | method
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol_name": self.symbol_name,
            "file_path": self.file_path,
            "kind": self.kind,
            "confidence": self.confidence,
        }


class BilingualSemanticLexicon:
    """Bilingual lexicon mapping natural language patterns to semantic concepts."""

    ACTION_PATTERNS = [
        ("create_feature", [
            r"\bbikin\b", r"\bbuat\b", r"\btambah\b", r"\badd\b", r"\bcreate\b",
            r"\bimplement\b", r"\bnew\b", r"\bfitur baru\b", r"\bpasang\b"
        ]),
        ("fix_bug", [
            r"\bperbaiki\b", r"\bbenerin\b", r"\bfix\b", r"\bdebug\b", r"\bpatch\b",
            r"\brusak\b", r"\berror\b", r"\bcrash\b", r"\bbug\b", r"\bgagal\b"
        ]),
        ("refactor", [
            r"\brefactor\b", r"\brombak\b", r"\bsederhanakan\b", r"\brestructure\b",
            r"\brapikan\b", r"\bclean\b"
        ]),
        ("design_ui", [
            r"\bdesain\b", r"\btampilan\b", r"\blayout\b", r"\bui\b", r"\bux\b",
            r"\btheme\b", r"\bhud\b", r"\bcanvas\b"
        ]),
        ("audit_review", [
            r"\bsisir\b", r"\bsisir kembali\b", r"\baudit\b", r"\btinjau\b", r"\bevaluasi\b",
            r"\bperiksa\b", r"\bcek\b", r"\binspect\b", r"\breview\b", r"\banalisa\b",
            r"\banalyze\b", r"\bbedah\b", r"\bselidiki\b"
        ]),
        ("calibrate", [
            r"\bkalibrasi\b", r"\bselaraskan\b", r"\bsinkronkan\b", r"\balign\b",
            r"\bsync\b", r"\bupdate\b", r"\bperbarui\b", r"\btingkatkan\b"
        ]),
        ("delete", [
            r"\bhapus\b", r"\bdelete\b", r"\bremove\b", r"\bdrop\b", r"\bbuang\b"
        ]),
    ]

    RISK_PATTERNS = [
        ("collision", [r"\bbentrok\b", r"\bduplikat\b", r"\bconflict\b", r"\bdouble\b", r"\btabrakan\b"]),
        ("regression", [r"\brusak\b", r"\bhilang\b", r"\bregress\b", r"\bpecah\b"]),
        ("performance", [r"\blambat\b", r"\blemot\b", r"\blag\b", r"\bkenceng\b", r"\bslow\b", r"\btimeout\b"]),
        ("overflow", [r"\btumpah\b", r"\bkeluar kotak\b", r"\boverflow\b", r"\bclipping\b"]),
        ("shallow_gimmick", [
            r"\bgimmick\b", r"\bminim\b", r"\bterbatas\b", r"\bdangkal\b",
            r"\bshallow\b", r"\bsuperficial\b", r"\btidak memberikan kontribusi\b",
            r"\btanpa kontribusi\b", r"\btanpa dampak\b"
        ]),
    ]

    NEGATION_PRESERVATION_PATTERNS = [
        r"jangan\s+(?:sampai\s+)?(?:ubah|hapus|sentuh|rusak|timpa|bentrok)",
        r"dilarang\s+(?:ubah|hapus|sentuh)",
        r"tanpa\s+(?:merusak|mengubah|menghapus)",
        r"do\s+not\s+(?:modify|touch|delete|break)",
        r"don't\s+(?:modify|touch|delete|break)",
        r"preserve\b",
        r"tetap\s+pertahankan\b",
    ]

    VAGUE_ADJECTIVES = {
        "keren", "bagus", "mantap", "kenceng", "enak", "cantik", "oke", "rapi", "rapikan",
        "better", "cool", "cleaner", "faster", "nice", "proper", "optimal", "fleksibel"
    }

    CONCEPT_SYNONYMS = {
        "ukur sudut": ["angle_measure", "protractor", "angle", "measure"],
        "sudut": ["angle", "protractor"],
        "tombol": ["button", "control", "trigger"],
        "toolbar": ["toolbar", "dock", "navbar"],
        "canvas": ["canvas", "stage", "viewport"],
        "layar": ["screen", "view", "window"],
        "reset": ["reset", "clear"],
        "auth": ["auth", "session", "login", "token"],
        "semantik": ["semantics", "semantic", "semantic_bridge", "ontology", "intermediate_representation", "semantic_ir"],
        "semantic": ["semantics", "semantic", "semantic_bridge", "ontology", "intermediate_representation", "semantic_ir"],
        "skill": ["skill", "skills", "goby-universal", "panduan", "instructions"],
        "skills": ["skill", "skills", "goby-universal", "panduan", "instructions"],
        "kontrak": ["contract", "invariant", "obligation", "preservation"],
        "anchor": ["project_anchor", "identity_anchor", "ground_of_being"],
        "exemplar": ["exemplar_generalizer", "anti_parroting", "variation"],
        "depth": ["depth_engine", "architectural_depth", "mdi"],
        "collision": ["capability_registry", "anti_collision"],
    }


class TripartiteSemanticBridge:
    """
    Main engine connecting Natural Language, Semantic Intent Ontologies,
    and Concrete Repository AST Symbols.
    """

    def __init__(self, symbol_map: Optional[SymbolMap] = None):
        self.symbol_map = symbol_map or SymbolMap()
        self.lexicon = BilingualSemanticLexicon()

    def normalize_phrase(self, text: str) -> NormalizedConcept:
        """Translates a raw prompt phrase into a structured NormalizedConcept."""
        text_lower = text.lower()

        # 1. Action detection
        detected_action = "unknown"
        for act, patterns in self.lexicon.ACTION_PATTERNS:
            if any(re.search(pat, text_lower) for pat in patterns):
                detected_action = act
                break

        # 2. Risk detection
        risk_flags = []
        for risk, patterns in self.lexicon.RISK_PATTERNS:
            if any(re.search(pat, text_lower) for pat in patterns):
                risk_flags.append(risk)

        # 3. Preservation & Negation detection
        has_preservation = any(
            re.search(pat, text_lower) for pat in self.lexicon.NEGATION_PRESERVATION_PATTERNS
        )

        preserved_targets = []
        if has_preservation:
            # Extract potential file names or symbols near preservation clauses
            file_candidates = re.findall(r"[\w/\.-]+\.(?:tsx|jsx|ts|js|py|css|html|json)", text)
            preserved_targets.extend(file_candidates)

        # 4. Keyword extraction with concept synonyms
        keywords = set()
        for phrase, syns in self.lexicon.CONCEPT_SYNONYMS.items():
            if phrase in text_lower:
                keywords.update(syns)

        # Also extract identifier tokens (CamelCase or snake_case or dotted words)
        words = re.findall(r"\b[A-Za-z0-9_\.-]+\b", text)
        for w in words:
            if "." in w or "_" in w or (any(c.isupper() for c in w) and any(c.islower() for c in w)):
                keywords.add(w)

        return NormalizedConcept(
            action=detected_action,
            keywords=sorted(list(keywords)),
            has_preservation=has_preservation,
            preserved_targets=preserved_targets,
            risk_flags=risk_flags,
            raw_text=text,
        )

    def classify_token_ambiguity(self, token: str, action: str = "create_feature") -> str:
        """
        Disambiguates whether a token represents:
        - 'vague': Abstract buzzword/adjective with no technical grounding or parameter.
        - 'new_entity': Concrete target symbol or domain noun to create.
        - 'grounded': Concrete entity already present or specified with clear parameters.
        """
        token_clean = token.strip()
        low = token_clean.lower()

        # Check for vague buzzwords
        words = low.split()
        if any(w in self.lexicon.VAGUE_ADJECTIVES for w in words):
            # If it's purely an adjective phrase without concrete noun
            has_concrete_noun = any(
                ("tool" in w or "modul" in w or "kompresi" in w or "." in w or "_" in w)
                for w in words
            )
            if not has_concrete_noun:
                return "vague"

        # Check for PascalCase / camelCase / file extension / concrete technical nouns
        is_pascal_case = bool(re.match(r"^[A-Z][a-zA-Z0-9]+$", token_clean))
        has_file_ext = bool(re.search(r"\.(tsx|jsx|ts|js|py|css|html|json)$", token_clean))
        has_technical_noun = any(
            t in low for t in ["modul", "fungsi", "kompresi", "router", "service", "handler", "manager"]
        )

        if is_pascal_case or has_file_ext or has_technical_noun:
            return "new_entity"

        return "grounded"

    def resolve_ast_entities(self, keywords: List[str]) -> List[ResolvedASTEntity]:
        """
        Resolves semantic keywords against the active SymbolMap to locate concrete
        symbols and source files in the repository.
        """
        resolved: List[ResolvedASTEntity] = []
        seen = set()

        # Expand keywords with concept synonyms if available
        expanded_keywords = set()
        for kw in keywords:
            expanded_keywords.add(kw.lower())
            for phrase, syns in self.lexicon.CONCEPT_SYNONYMS.items():
                if kw.lower() in syns or kw.lower() == phrase:
                    expanded_keywords.update(syns)
                    expanded_keywords.add(phrase)

        for kw in expanded_keywords:
            # 1. Search symbols
            matching_syms = self.symbol_map.find_symbol(kw)
            for sym in matching_syms:
                key = (sym.name, sym.file_path)
                if key not in seen:
                    seen.add(key)
                    resolved.append(
                        ResolvedASTEntity(
                            symbol_name=sym.name,
                            file_path=sym.file_path,
                            kind=sym.kind,
                            confidence=0.9,
                        )
                    )

            # 2. Search file paths directly
            for fp in self.symbol_map.files.keys():
                fp_norm = fp.replace("\\", "/").lower()
                if kw in fp_norm:
                    key = (fp, fp)
                    if key not in seen:
                        seen.add(key)
                        resolved.append(
                            ResolvedASTEntity(
                                symbol_name=fp.split("/")[-1],
                                file_path=fp,
                                kind="file",
                                confidence=0.85,
                            )
                        )

        return resolved
