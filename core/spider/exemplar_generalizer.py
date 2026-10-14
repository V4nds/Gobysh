"""
Exemplar Generalizer Engine for Goby v5.6.
Provides concept lifting, contextual variation expansion, and anti-parroting
guardrail synthesis for user-provided exemplars.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set


@dataclass
class ExemplarInductionResult:
    """Result of exemplar concept lifting and expansion."""
    inferred_domain: str
    original_exemplars: List[str]
    variations: List[str] = field(default_factory=list)
    guardrail_rule: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inferred_domain": self.inferred_domain,
            "original_exemplars": self.original_exemplars,
            "variations": self.variations,
            "guardrail_rule": self.guardrail_rule,
        }


class ExemplarGeneralizer:
    """
    Exemplar Induction and Anti-Parroting Synthesizer.
    Analyzes illustrative user examples, lifts them into abstract conceptual domains,
    generates complementary variations, and emits anti-literalism guardrails.
    """

    KNOWN_DOMAINS = [
        (
            "geometric_measurement_tools",
            [
                r"\b(penggaris|busur|jangka|sudut|meteran|ruler|protractor|compass|caliper)\b",
                r"\b(measure|measurement|dimension|grid|scale)\b",
            ],
            ["jangka (arc tool)", "digital caliper (jarak presisi)", "angle gauge (sudut dinamis)", "coordinate inspector"]
        ),
        (
            "authentication_strategies",
            [
                r"\b(jwt|session|oauth|token|cookie|sso|bearer|saml|auth)\b",
                r"\b(login|credential|identity|password)\b",
            ],
            ["oauth2_provider (PKCE)", "api_key_authenticator", "session_store_redis", "mfa_authenticator"]
        ),
        (
            "data_export_formats",
            [
                r"\b(svg|png|pdf|json|csv|xml|markdown|html)\b",
                r"\b(export|download|serialize|dump)\b",
            ],
            ["pdf_document_generator", "csv_tabular_export", "standalone_svg_vector", "json_schema_export"]
        ),
        (
            "layout_archetypes",
            [
                r"\b(bento|grid|flex|card|hud|dock|panel|drawer|modal)\b",
                r"\b(layout|container|frame|tile)\b",
            ],
            ["contextual_hud_overlay", "adaptive_bento_grid", "collapsible_inspector_dock", "fluid_data_list"]
        ),
        (
            "cache_storage_backends",
            [
                r"\b(redis|memcached|in_memory|sqlite|indexeddb|localstorage)\b",
                r"\b(cache|store|persist|state)\b",
            ],
            ["tiered_lru_memory_cache", "persistent_indexeddb_store", "atomic_file_backed_cache"]
        ),
    ]

    def induce_and_expand(self, exemplars: List[str]) -> ExemplarInductionResult:
        """
        Lifts a list of exemplars into a conceptual domain, computes complementary
        variations, and synthesizes an anti-parroting rule.
        """
        if not exemplars:
            return ExemplarInductionResult(
                inferred_domain="generic",
                original_exemplars=[],
                variations=[],
                guardrail_rule="",
            )

        combined_text = " ".join(exemplars).lower()
        matched_domain: Optional[str] = None
        variations: List[str] = []

        # 1. Match against known domain patterns
        for domain_name, patterns, domain_variations in self.KNOWN_DOMAINS:
            for pat in patterns:
                if re.search(pat, combined_text):
                    matched_domain = domain_name
                    # Filter variations to avoid returning what the user already mentioned
                    variations = [
                        v for v in domain_variations
                        if not any(ex.lower() in v.lower() for ex in exemplars)
                    ]
                    break
            if matched_domain:
                break

        # 2. Fallback if no specific domain matched
        if not matched_domain:
            clean_token = re.sub(r'[^a-zA-Z0-9_]+', '_', exemplars[0]).strip('_').lower()
            matched_domain = f"custom_{clean_token}_concept"
            variations = [
                f"{clean_token}_extended_variant_1",
                f"{clean_token}_extended_variant_2",
            ]

        # 3. Formulate Anti-Parroting Blueprint Rule
        examples_str = ", ".join([f"'{e}'" for e in exemplars])
        variations_str = ", ".join([f"'{v}'" for v in variations[:3]])
        rule = (
            f"ANTI_PARROTING_EXEMPLAR_INDUCTION: User-provided examples [{examples_str}] are illustrative exemplars of domain '{matched_domain}'. "
            f"Do NOT hardcode literal copies of only these examples. Design an extensible abstraction and provide varied contextual capabilities (e.g. {variations_str})."
        )

        return ExemplarInductionResult(
            inferred_domain=matched_domain,
            original_exemplars=exemplars,
            variations=variations,
            guardrail_rule=rule,
        )
