"""
Code-Semantic Mapper Engine for Gobysh v5.1.
Bridges formal Semantic IR and constraints to concrete repository symbols and files.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from core.semantics.dependency_graph import DependencyGraph

from core.semantics.intermediate_representation import SemanticEntity
from core.semantics.specification import Requirement
from core.translation.symbol_mapper import Symbol, SymbolMap


STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
    "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "and", "or", "not", "but", "if", "so", "as", "it", "this", "that",
    "fix", "add", "update", "modify", "delete", "remove", "change",
    "buat", "tambah", "ubah", "hapus", "perbaiki", "pada", "dan", "atau",
    "di", "ke", "dari", "yang", "untuk", "dengan", "ini", "itu",
}


@dataclass
class MappingReport:
    """Detailed report of mapped symbols, target files, and dependency blast radius."""
    matched_symbols: List[Symbol] = field(default_factory=list)
    target_files: List[str] = field(default_factory=list)
    impacted_dependents: List[str] = field(default_factory=list)
    protected_symbols_violated: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_symbols": [s.to_dict() for s in self.matched_symbols],
            "target_files": self.target_files,
            "impacted_dependents": self.impacted_dependents,
            "protected_symbols_violated": self.protected_symbols_violated,
        }


class CodeSemanticMapper:
    """Maps high-level intent/IR to code symbols, target files, and impact radius."""

    def __init__(self, symbol_map: SymbolMap, dependency_graph: "DependencyGraph"):
        self.symbol_map = symbol_map
        self.dependency_graph = dependency_graph

    def _extract_tokens(self, text: str) -> List[str]:
        words = re.findall(r"[A-Za-z0-9_]+", text)
        tokens: List[str] = []
        for w in words:
            low = w.lower()
            if len(low) >= 2 and low not in STOP_WORDS:
                tokens.append(low)
                # Split camelCase / snake_case into sub-tokens
                sub_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", w)
                for sp in sub_parts:
                    sp_low = sp.lower()
                    if len(sp_low) >= 3 and sp_low not in STOP_WORDS and sp_low not in tokens:
                        tokens.append(sp_low)
        return tokens

    def map_query(
        self,
        query: str,
        protected_symbols: Optional[List[str]] = None,
    ) -> MappingReport:
        """Map a free-form query or instruction into symbols, target files, and impacted files."""
        tokens = self._extract_tokens(query)
        # Also include whole words from query
        raw_words = [w.strip() for w in re.split(r"\s+", query) if len(w.strip()) >= 2]
        return self._resolve_mapping(tokens, raw_words, protected_symbols=protected_symbols)

    def map_intent(
        self,
        entities: Optional[List[SemanticEntity]] = None,
        requirements: Optional[List[Requirement]] = None,
        protected_symbols: Optional[List[str]] = None,
    ) -> MappingReport:
        """Map formal semantic entities and requirements into code mapping."""
        tokens: List[str] = []
        raw_words: List[str] = []

        if entities:
            for ent in entities:
                tokens.extend(self._extract_tokens(ent.name))
                raw_words.append(ent.name)
                if ent.entity_type:
                    tokens.extend(self._extract_tokens(ent.entity_type))

        if requirements:
            for req in requirements:
                tokens.extend(self._extract_tokens(req.description))
                raw_words.append(req.description)

        return self._resolve_mapping(tokens, raw_words, protected_symbols=protected_symbols)

    def _resolve_mapping(
        self,
        tokens: List[str],
        raw_phrases: List[str],
        protected_symbols: Optional[List[str]] = None,
    ) -> MappingReport:
        matched_symbols: List[Symbol] = []
        target_files: Set[str] = set()
        seen_sym_keys: Set[str] = set()

        search_tokens = set(tokens)

        # 1. Match symbols across all files
        for file_path, fmap in self.symbol_map.files.items():
            norm_file = file_path.replace("\\", "/").strip("./").strip("/")
            file_matched = False

            # Check if filename/path itself matches any search token
            for t in search_tokens:
                if t in norm_file.lower():
                    target_files.add(norm_file)
                    file_matched = True

            for sym in fmap.symbols:
                sym_name_low = sym.name.lower()
                sym_key = f"{norm_file}::{sym.name}::{sym.line_start}"

                is_match = False
                # Direct or substring match
                for t in search_tokens:
                    if t == sym_name_low or t in sym_name_low or sym_name_low in t:
                        is_match = True
                        break

                # Phrase match
                if not is_match:
                    for phrase in raw_phrases:
                        if sym.name.lower() in phrase.lower():
                            is_match = True
                            break

                if is_match and sym_key not in seen_sym_keys:
                    seen_sym_keys.add(sym_key)
                    matched_symbols.append(sym)
                    target_files.add(norm_file)

        sorted_target_files = sorted(list(target_files))

        # 2. Compute downstream blast radius
        impacted_dependents: Set[str] = set()
        for tf in sorted_target_files:
            deps = self.dependency_graph.get_downstream_dependents(tf)
            for d in deps:
                if d not in target_files:
                    impacted_dependents.add(d)
        sorted_impacted = sorted(list(impacted_dependents))

        # 3. Check protected symbol violations
        prot_syms = protected_symbols or []
        violated_syms: Set[str] = set()

        if prot_syms:
            affected_by_graph = self.dependency_graph.find_affected_protected_symbols(
                sorted_target_files, prot_syms
            )
            violated_syms.update(affected_by_graph)

            # Also check direct symbol matches
            for sym in matched_symbols:
                for ps in prot_syms:
                    if ps.lower() == sym.name.lower() or ps.lower() in sym.name.lower():
                        violated_syms.add(ps)

        return MappingReport(
            matched_symbols=matched_symbols,
            target_files=sorted_target_files,
            impacted_dependents=sorted_impacted,
            protected_symbols_violated=sorted(list(violated_syms)),
        )
