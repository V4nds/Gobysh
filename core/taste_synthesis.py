import dataclasses
from typing import List, Dict

@dataclasses.dataclass
class HeuristicEvaluation:
    """
    Result of the right-brain Taste Synthesis Engine evaluation.
    """
    is_slop: bool
    spatial_score: int
    motion_score: int
    visual_score: int
    genjutsu_score: int
    total_score: int
    detected_keywords: List[str]
    bypass_suggestion: str


class ModernCSSKeywordHeuristic:
    """
    Modern Design Keyword Presence Heuristics Engine.
    Evaluates UI/UX code snippets by counting the presence of modern design vocabulary indicators (CSS Flex/Grid, Transitions, Backdrop Filters, WebGL Canvas).
    Note: This is a simple keyword counter and does not perform actual AST/CSS parsing or deep visual evaluation.
    """

    DIMENSIONS = {
        "spatial": ["flex", "grid", "clamp", "calc", "bento", "auto-layout", "gap-"],
        "motion": ["transition", "transform", "hover:", "gsap", "motion", "animate", "stagger"],
        "visual": ["opacity", "shadow", "gradient", "backdrop", "backdrop-filter", "var(--", "glass", "blur"],
        "genjutsu": ["three", "canvas", "webgl", "particles", "lottie", "orbit"]
    }

    @classmethod
    def evaluate(cls, code: str) -> HeuristicEvaluation:
        """
        Evaluate UI code string and return a multi-dimensional design score.
        """
        code_lower = code.lower()
        
        detected_keywords = []
        scores = {"spatial": 0, "motion": 0, "visual": 0, "genjutsu": 0}

        for dim, keywords in cls.DIMENSIONS.items():
            for kw in keywords:
                if kw in code_lower:
                    scores[dim] += 1
                    detected_keywords.append(kw)

        # Remove duplicates
        detected_keywords = list(set(detected_keywords))
        
        total_score = sum(scores.values())
        
        # Determine if the code is 'slop' (lacking basic modern aesthetics)
        # We expect at least some spatial awareness and visual/motion traits,
        # UNLESS the code is heavily relying on Genjutsu (WebGL/ThreeJS canvas logic).
        is_slop = (total_score < 3 or (scores["spatial"] == 0 and scores["visual"] == 0)) and scores["genjutsu"] < 2

        # Construct bypass logic suggestion if it's slop
        bypass_suggestion = ""
        if is_slop:
            bypass_suggestion = (
                "Taste Synthesis Bypass Triggered! The design is rigid (slop). "
                "Inject UI/UX Pro Max: Use Bento Box grids & clamp() for layout. "
                "Inject GSAP for motion. Inject Layered Shadows & Glassmorphism for depth."
            )
        elif total_score < 6:
            bypass_suggestion = (
                "Design is acceptable but lacks Genjutsu factor. Consider adding "
                "ThreeJS particles or advanced GSAP stagger animations."
            )

        return HeuristicEvaluation(
            is_slop=is_slop,
            spatial_score=scores["spatial"],
            motion_score=scores["motion"],
            visual_score=scores["visual"],
            genjutsu_score=scores["genjutsu"],
            total_score=total_score,
            detected_keywords=detected_keywords,
            bypass_suggestion=bypass_suggestion
        )


@dataclasses.dataclass
class DensityEvaluation:
    """Evaluation result of the Visual Density & Anti-Boxification Governor."""
    is_over_encapsulated: bool
    boxification_score: int
    wrapper_depth: int
    detected_anti_patterns: List[str]
    suggestion: str


class VisualDensityGovernor:
    """
    Evaluates UI markup for over-encapsulation (boxification) and information density.
    Prevents AI models from forcing all telemetry, symbols, and explanatory text into
    rigid nested card/box components instead of clean, contextual layouts.
    """

    BOX_CONTAINER_PATTERNS = [
        r'class(?:name)?=["\'][^"\']*\b(?:card|box|frame|panel|widget|bento-card|tile)\b[^"\']*["\']',
        r'class(?:name)?=["\'][^"\']*\b(?:p-[0-9]+|rounded-[a-z0-9]+|shadow-[a-z0-9]+|border)\b[^"\']*["\']',
    ]

    @classmethod
    def evaluate(cls, code: str) -> DensityEvaluation:
        import re
        code_lower = code.lower()
        anti_patterns = []
        boxification_score = 0

        # Check for generic container nesting
        div_openings = len(re.findall(r'<div\b', code_lower))
        semantic_tags = len(re.findall(r'<(?:header|main|nav|aside|footer|output|meter|canvas|svg|table|ul|ol|li)\b', code_lower))

        if div_openings >= 5 and semantic_tags == 0:
            anti_patterns.append("Excessive generic div containers without semantic layout elements.")
            boxification_score += 2

        # Check for isolated single-value cards
        single_val_card_pat = r'<div[^>]*class(?:name)?=["\'][^"\']*\bcard\b[^"\']*["\'][^>]*>\s*<p[^>]*>[^<]+</p>\s*<(?:span|h[1-6]|p)[^>]*>[^<]+</(?:span|h[1-6]|p)>\s*</div>'
        single_val_cards = len(re.findall(single_val_card_pat, code_lower))
        if single_val_cards >= 3:
            anti_patterns.append(f"Detected {single_val_cards} isolated single-value cards. Use an integrated telemetry HUD or clean data-list.")
            boxification_score += 3

        # Deeply nested container wrappers without content
        nested_div_pat = r'<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>'
        if re.search(nested_div_pat, code_lower):
            anti_patterns.append("Deeply nested container wrappers (> 3 levels) detected.")
            boxification_score += 3

        is_over_encapsulated = boxification_score >= 3
        suggestion = ""
        if is_over_encapsulated:
            suggestion = (
                "Anti-Boxification Guardrail: Avoid wrapping every individual symbol or label into nested card/frame boxes. "
                "Use contextual inline HUDs, direct CSS Grid/Flex layouts, and semantic HTML elements (<output>, <meter>, <dl>)."
            )

        return DensityEvaluation(
            is_over_encapsulated=is_over_encapsulated,
            boxification_score=boxification_score,
            wrapper_depth=div_openings,
            detected_anti_patterns=anti_patterns,
            suggestion=suggestion,
        )

