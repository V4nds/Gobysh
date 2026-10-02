"""
Advanced Bilingual Negation Handler for Gobysh v5.1.
Extracts negative constraints, forbidden targets, and preservation directives
from complex Indonesian and English natural language inputs.
"""

from dataclasses import dataclass, field
import re
from typing import List


@dataclass
class NegationResult:
    """Structured extraction of user negative directives."""
    forbidden_targets: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    preserve_demanded: bool = False
    negative_phrases: List[str] = field(default_factory=list)


class NegationHandler:
    """Extractor for bilingual negation boundaries."""

    # Regex patterns for negative target extraction
    _PATTERNS = [
        # Indonesian: jangan/tidak boleh/dilarang/tanpa [pernah/keras] ubah/sentuh/edit/hapus/ganti [file] <target>
        r'(?:jangan|tidak boleh|dilarang(?:\s+keras)?|tanpa)\s+(?:pernah\s+)?(?:ubah|mengubah|ganti|edit|sentuh|menyentuh|hapus|menghapus|merusak)\s+(?:file\s+|tabel\s+|table\s+)?([a-zA-Z0-9_./\-]+)',
        # Indonesian: jangan [pernah] sentuh <target>
        r'(?:jangan|tidak boleh|dilarang)\s+(?:pernah\s+)?(?:sentuh|menyentuh)\s+([a-zA-Z0-9_./\-]+)',
        # English: do not/don't/never/without [ever] touch/modify/alter/change/delete/remove [file/table] <target>
        r'(?:do\s+not|don\'?t|never|without)\s+(?:ever\s+)?(?:touch|touching|modify|modifying|alter|altering|change|changing|delete|remove|removing)\s+(?:file\s+|table\s+)?([a-zA-Z0-9_./\-]+)',
        # English: forbidden to / prohibited from modifying <target>
        r'(?:forbidden\s+to|prohibited\s+from)\s+(?:touch|modify|change|edit)\s+([a-zA-Z0-9_./\-]+)',
    ]

    _PRESERVATION_MARKERS = [
        "tanpa menghapus", "tanpa merusak", "tanpa ubah method lama",
        "tanpa menghapus method", "tanpa menghapus fungsi", "preserve",
        "keep existing", "jangan hapus", "don't delete", "don't remove",
        "backward compatibility", "kompatibilitas", "legacy",
        "tanpa mengganggu", "without touching", "without breaking",
    ]

    @classmethod
    def parse_negations(cls, text: str) -> NegationResult:
        if not text:
            return NegationResult()

        text_lower = text.lower()
        forbidden_targets: List[str] = []
        negative_phrases: List[str] = []

        # 1. Extract targets matching negative patterns
        for pat in cls._PATTERNS:
            for match in re.finditer(pat, text_lower):
                target = match.group(1).strip()
                phrase = match.group(0).strip()
                if target and target not in ("file", "table", "tabel", "fungsi", "method", "ini"):
                    if target not in forbidden_targets:
                        forbidden_targets.append(target)
                if phrase not in negative_phrases:
                    negative_phrases.append(phrase)

        # 2. Check preservation demand
        preserve_demanded = any(m in text_lower for m in cls._PRESERVATION_MARKERS)

        return NegationResult(
            forbidden_targets=forbidden_targets,
            preserve_demanded=preserve_demanded,
            negative_phrases=negative_phrases,
        )
