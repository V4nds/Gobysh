import ast
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.ccr_engine import NeuronSignal, GateType

def neuron_info_density(self, text: str) -> NeuronSignal:
    """
    Signal: Raw text statistics for AI to judge substance vs filler.
    Mechanism: Word counting, lexical diversity, filler phrase detection.

    SOFT SIGNAL — returns raw metrics, AI interprets.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)

    if total_words == 0:
        return NeuronSignal(
            neuron_name="DENSITY",
            gate_type=GateType.SOFT,
            passed=False,
            confidence=1.0,
            message="Text is empty.",
            evidence={"total_words": 0},
            suggestion="Provide substantive content.",
        )

    unique_words = set(words)
    lexical_diversity = len(unique_words) / total_words

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_length = total_words / max(len(sentences), 1)

    # Count filler phrase occurrences
    text_lower = text.lower()
    filler_counts: Dict[str, int] = {}
    total_filler_hits = 0
    for filler in self.FILLER_PHRASES:
        count = text_lower.count(filler)
        if count > 0:
            filler_counts[filler] = count
            total_filler_hits += count

    filler_ratio = total_filler_hits / max(len(sentences), 1)

    return NeuronSignal(
        neuron_name="DENSITY",
        gate_type=GateType.SOFT,
        passed=True,  # Always "passes" — AI decides from raw data
        confidence=lexical_diversity,
        message=(
            f"Words: {total_words}, Unique: {len(unique_words)}, "
            f"Diversity: {lexical_diversity:.2%}, "
            f"Avg sentence: {avg_sentence_length:.1f} words, "
            f"Filler hits: {total_filler_hits}"
        ),
        evidence={
            "total_words": total_words,
            "unique_words": len(unique_words),
            "lexical_diversity": round(lexical_diversity, 3),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "sentence_count": len(sentences),
            "filler_phrase_counts": filler_counts,
            "total_filler_hits": total_filler_hits,
            "filler_ratio_per_sentence": round(filler_ratio, 2),
        },
        suggestion="",
    )


def neuron_consistency(self, text: str) -> NeuronSignal:
    """
    Signal: Extract claims, detect numeric conflicts and negation pairs.
    Mechanism: Regex-based claim and number extraction.

    SOFT SIGNAL — returns extracted data, AI judges contradictions.
    """
    claims: List[Dict[str, Any]] = []
    numeric_conflicts: List[Dict[str, Any]] = []
    negation_pairs: List[Dict[str, Any]] = []

    lines = text.split("\n")

    # --- Extract numeric claims ---
    number_pattern = re.compile(
        r'(\b\w[\w\s]{2,30})\b(?:adalah|=|:|\bsebesar\b|\bof\b|\bis\b)\s*(\d+[\d.,]*\s*\w*)',
        re.IGNORECASE,
    )
    numeric_claims: List[Tuple[str, str, int]] = []
    for line_no, line in enumerate(lines, 1):
        for match in number_pattern.finditer(line):
            context = match.group(1).strip().lower()
            value = match.group(2).strip()
            claims.append({"text": match.group(0).strip(), "line": line_no, "type": "numeric"})
            numeric_claims.append((context, value, line_no))

    # Check for conflicting numbers with same context
    seen_contexts: Dict[str, List[Tuple[str, int]]] = {}
    for context, value, line_no in numeric_claims:
        key = re.sub(r'\s+', ' ', context)[:30]
        if key not in seen_contexts:
            seen_contexts[key] = []
        seen_contexts[key].append((value, line_no))

    for context, values in seen_contexts.items():
        if len(values) >= 2:
            unique_vals = set(v for v, _ in values)
            if len(unique_vals) > 1:
                numeric_conflicts.append({
                    "context": context,
                    "values": [{"value": v, "line": ln} for v, ln in values],
                })

    # --- Extract negation pairs ---
    negation_patterns = [
        (r'(?:mendukung|support)\s+(.+)', r'(?:tidak|not)\s+(?:mendukung|support|kompatibel|compatible)\s+(.+)'),
        (r'(?:menggunakan|using|use)\s+(.+)', r'(?:tidak|not)\s+(?:menggunakan|using|use)\s+(.+)'),
    ]

    positive_claims: List[Tuple[str, int]] = []
    negative_claims: List[Tuple[str, int]] = []

    for line_no, line in enumerate(lines, 1):
        for pos_pattern, neg_pattern in negation_patterns:
            pos_match = re.search(pos_pattern, line, re.IGNORECASE)
            neg_match = re.search(neg_pattern, line, re.IGNORECASE)
            if pos_match:
                positive_claims.append((pos_match.group(0), line_no))
            if neg_match:
                negative_claims.append((neg_match.group(0), line_no))

    for pos_text, pos_line in positive_claims:
        for neg_text, neg_line in negative_claims:
            if pos_line != neg_line:
                negation_pairs.append({
                    "positive": {"text": pos_text, "line": pos_line},
                    "negative": {"text": neg_text, "line": neg_line},
                })

    has_issues = len(numeric_conflicts) > 0 or len(negation_pairs) > 0

    return NeuronSignal(
        neuron_name="CONSISTENCY",
        gate_type=GateType.SOFT,
        passed=True,  # Always "passes" — AI judges from data
        confidence=0.6 if has_issues else 0.9,
        message=(
            f"Claims extracted: {len(claims)}. "
            f"Numeric conflicts: {len(numeric_conflicts)}. "
            f"Negation pairs: {len(negation_pairs)}."
        ),
        evidence={
            "claims": claims[:20],
            "numeric_conflicts": numeric_conflicts,
            "negation_pairs": negation_pairs,
            "total_lines_analyzed": len(lines),
        },
        suggestion=(
            f"Found {len(numeric_conflicts)} numeric conflict(s) and "
            f"{len(negation_pairs)} potential negation pair(s). Review carefully."
            if has_issues else ""
        ),
    )

