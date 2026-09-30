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


def neuron_semantic_alignment(
    self,
    code: str,
    contract: Optional[Any] = None,
    original_code: Optional[str] = None
) -> NeuronSignal:
    """
    Signal: Does this code faithfully adhere to semantic constraints,
    scope relevance, and Indonesian intent traits?

    Evaluates:
      1. Faithfulness (0.0 - 1.0): No forbidden target mutations, no unauthorized symbol deletions.
      2. Context Relevance (0.0 - 1.0): Scope containment to target domains.
      3. Semantic Similarity (0.0 - 1.0): Requested action traits realized in AST.
    """
    if not code or not code.strip():
        return NeuronSignal(
            neuron_name="SEMANTIC_ALIGNMENT",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=1.0,
            message="No code provided for semantic alignment evaluation.",
            evidence={"faithfulness_score": 1.0, "context_relevance_score": 1.0, "semantic_similarity_score": 1.0},
        )

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return NeuronSignal(
            neuron_name="SEMANTIC_ALIGNMENT",
            gate_type=GateType.HARD,
            passed=False,
            confidence=1.0,
            message=f"Syntax error prevents semantic alignment check: {e.msg} at line {e.lineno}",
            evidence={"error": str(e), "faithfulness_score": 0.0, "context_relevance_score": 0.0, "semantic_similarity_score": 0.0},
            suggestion="Fix syntax errors before running semantic evaluation.",
        )

    if contract is None:
        return NeuronSignal(
            neuron_name="SEMANTIC_ALIGNMENT",
            gate_type=GateType.SOFT,
            passed=True,
            confidence=1.0,
            message="No semantic contract provided; default alignment passed.",
            evidence={"faithfulness_score": 1.0, "context_relevance_score": 1.0, "semantic_similarity_score": 1.0},
        )

    violations = []
    faithfulness = 1.0
    relevance = 1.0
    similarity = 1.0

    # 1. Faithfulness: Forbidden targets
    defined_symbols = set()
    referenced_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_symbols.add(node.name.lower())
        elif isinstance(node, ast.ClassDef):
            defined_symbols.add(node.name.lower())
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id.lower())

    for target in contract.forbidden_targets:
        target_clean = re.sub(r'\.(py|js|ts|json|md)$', '', target).lower()
        if any(target_clean in sym for sym in defined_symbols) or any(target_clean in ref for ref in referenced_names):
            faithfulness -= 0.6
            violations.append(f"Forbidden target modified/accessed: '{target}'")

    # 1b. Faithfulness: Preservation of existing methods
    if contract.preserve_existing and original_code:
        try:
            orig_tree = ast.parse(original_code)
            orig_funcs = {
                n.name for n in ast.walk(orig_tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
            new_funcs = {
                n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
            missing = orig_funcs - new_funcs
            if missing:
                faithfulness = min(faithfulness - 0.6, 0.4)
                violations.append(f"Deleted existing symbol(s) despite preservation constraint: {list(missing)}")
        except Exception:
            pass

    faithfulness = max(0.0, min(1.0, round(faithfulness, 2)))

    # 2. Context Relevance: Strict scope containment
    if contract.strict_scope:
        matched_scope_hits = 0
        all_text = code.lower()
        for scope_item in contract.strict_scope:
            if scope_item.lower() in all_text or any(scope_item.lower() in sym for sym in defined_symbols):
                matched_scope_hits += 1
        relevance = matched_scope_hits / len(contract.strict_scope)
        relevance = max(0.2, min(1.0, round(relevance, 2)))

    # 3. Semantic Similarity: Expected traits realized in AST
    matched_traits = []
    if contract.expected_traits:
        for trait in contract.expected_traits:
            if trait == "validation":
                has_check = any(isinstance(n, (ast.If, ast.Assert, ast.Raise)) for n in ast.walk(tree))
                has_val_func = any("valid" in s or "check" in s or "verify" in s for s in defined_symbols)
                if has_check or has_val_func:
                    matched_traits.append("validation")
            elif trait == "auth":
                has_auth = any("auth" in s or "login" in s or "token" in s for s in defined_symbols) or "token" in code.lower() or "auth" in code.lower()
                if has_auth:
                    matched_traits.append("auth")
            elif trait == "refactor":
                if defined_symbols:
                    matched_traits.append("refactor")
            elif trait == "testing":
                has_test = any("test" in s for s in defined_symbols) or any(isinstance(n, ast.Assert) for n in ast.walk(tree))
                if has_test:
                    matched_traits.append("testing")
            elif trait == "security":
                has_sec = any(w in code.lower() for w in ["sanitize", "escape", "clean", "secure", "hash"])
                if has_sec:
                    matched_traits.append("security")
            elif trait == "documentation":
                has_doc = any(ast.get_docstring(n) is not None for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Module)))
                if has_doc:
                    matched_traits.append("documentation")

        similarity = len(matched_traits) / len(contract.expected_traits)
        similarity = round(similarity, 2)

    composite_score = round(0.4 * faithfulness + 0.3 * relevance + 0.3 * similarity, 2)
    passed = faithfulness >= 0.5 and composite_score >= 0.6
    gate_type = GateType.HARD if faithfulness < 0.5 else GateType.SOFT

    message = (
        f"Semantic Alignment: {composite_score:.0%} "
        f"(Faithfulness: {faithfulness:.0%}, Relevance: {relevance:.0%}, Similarity: {similarity:.0%})."
    )
    if violations:
        message += f" Violations: {'; '.join(violations)}."

    suggestion = ""
    if not passed:
        if faithfulness < 0.5:
            suggestion = f"BLOCKED: Faithfulness violation. Do not modify forbidden targets or remove preserved symbols: {violations}."
        elif similarity < 0.5:
            suggestion = f"Missing expected semantic traits: {[t for t in contract.expected_traits if t not in matched_traits]}."

    return NeuronSignal(
        neuron_name="SEMANTIC_ALIGNMENT",
        gate_type=gate_type,
        passed=passed,
        confidence=composite_score,
        message=message,
        evidence={
            "faithfulness_score": faithfulness,
            "context_relevance_score": relevance,
            "semantic_similarity_score": similarity,
            "composite_score": composite_score,
            "violations": violations,
            "matched_traits": matched_traits,
            "expected_traits": contract.expected_traits,
        },
        suggestion=suggestion,
    )


