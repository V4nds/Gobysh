import dataclasses
import re
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


@dataclasses.dataclass
class EditorialDiagramEvaluation:
    """Evaluation result of editorial diagram design heuristics (cathrynlavery/diagram-design standard)."""
    is_cluttered: bool
    density_score: int  # 1 to 10 scale (target is 4/10)
    focal_accent_count: int
    has_rainbow_accents: bool
    has_heavy_strokes: bool
    is_mermaid_slop: bool
    anti_patterns: List[str]
    editorial_suggestion: str


class EditorialDiagramHeuristic:
    """
    Editorial Visual Density & Anti-Slop Heuristic Engine.
    Codifies Cathryn Lavery's editorial diagram philosophy:
    - Target visual density: 4/10 (Above 9 nodes is cluttered; 2 nodes travelling together = 1 node).
    - Hairline stroke standard: 1px crisp hairlines (no heavy thick borders > 2px).
    - Focal accent discipline: 1-2 focal accents max (no rainbow slop with 5+ bright colors).
    - Mermaid anti-slop: Flags flat, un-styled, spaghetti Mermaid charts.
    """

    ACCENT_HEX_PATTERN = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b')
    NEUTRAL_HEXES = {
        "#fff", "#ffffff", "#000", "#000000",
        "#f5f5f5", "#f4f4f4", "#eeeeee", "#e5e5e5", "#e0e0e0", "#d4d4d4", "#cccccc",
        "#2d3142", "#1e1e1e", "#1a1a1a", "#222222", "#333333", "#444444", "#555555",
        "#666666", "#777777", "#888888", "#999999", "#aaaaaa", "#bbbbbb",
        "#111827", "#1f2937", "#374151", "#4b5563", "#6b7280", "#9ca3af", "#d1d5db", "#e5e7eb", "#f3f4f6", "#f9fafb"
    }

    @classmethod
    def evaluate(cls, code: str) -> EditorialDiagramEvaluation:
        code_lower = code.lower()
        anti_patterns = []
        is_mermaid_slop = False
        has_heavy_strokes = False
        has_rainbow_accents = False

        # 1. Check for Mermaid diagrams
        is_mermaid = any(kw in code_lower for kw in ["graph td", "graph lr", "graph tb", "graph rl", "flowchart td", "flowchart lr"])
        node_count = 0
        if is_mermaid:
            arrows = len(re.findall(r'-->|==>|-.->|->', code))
            node_defs = len(re.findall(r'\b[a-zA-Z0-9_-]+\[[^\]]+\]', code))
            node_count = max(node_defs, arrows // 2)
            has_subgraphs = "subgraph" in code_lower
            has_styling = any(kw in code_lower for kw in ["classdef", "style ", ":::"])

            # If > 8 nodes and flat spaghetti without subgraphs/styling
            if node_count > 8 and not has_subgraphs and not has_styling:
                is_mermaid_slop = True
                anti_patterns.append(f"Mermaid chart contains {node_count} nodes without subgraphs or semantic styling (Mermaid Slop).")

        # 2. Check for heavy strokes (> 2px) in SVG or CSS
        heavy_stroke_matches = re.findall(r'stroke-width=["\']([3-9]|[1-9][0-9]+)(?:px)?["\']', code_lower)
        heavy_border_matches = re.findall(r'border(?:-width)?:\s*([3-9]|[1-9][0-9]+)px', code_lower)
        if heavy_stroke_matches or heavy_border_matches:
            has_heavy_strokes = True
            anti_patterns.append("Heavy strokes (> 2px) detected. Use 1px crisp hairlines for clean editorial diagrams.")

        # 3. Check for accent color count (focal accents)
        all_hexes = [h.lower() for h in cls.ACCENT_HEX_PATTERN.findall(code)]
        accent_hexes = set(h for h in all_hexes if h not in cls.NEUTRAL_HEXES)
        focal_accent_count = len(accent_hexes)
        if focal_accent_count > 3:
            has_rainbow_accents = True
            anti_patterns.append(f"Found {focal_accent_count} distinct accent colors. Editorial discipline requires 1-2 focal accents; excess colors erase signal.")

        # 4. Target Density Score (1 to 10 scale)
        if node_count == 0:
            svg_shapes = len(re.findall(r'<(?:rect|circle|ellipse|path|polygon)\b', code_lower))
            if svg_shapes > 0:
                density_raw = min(10, max(1, svg_shapes // 3))
            else:
                density_raw = 4
        else:
            density_raw = min(10, max(1, (node_count * 10) // 12))

        density_score = density_raw
        is_cluttered = density_score >= 8 or is_mermaid_slop or has_rainbow_accents

        editorial_suggestion = ""
        if is_cluttered or is_mermaid_slop or has_heavy_strokes:
            editorial_suggestion = (
                "Diagram Design Editorial Standard: Target visual density 4/10. "
                "Use 1px crisp hairlines, 1-2 focal accents (Coral/Accent), and 4px grid spacing. "
                "If nodes > 9, split into two diagrams or use self-contained HTML/SVG architectural diagrams."
            )

        return EditorialDiagramEvaluation(
            is_cluttered=is_cluttered,
            density_score=density_score,
            focal_accent_count=focal_accent_count,
            has_rainbow_accents=has_rainbow_accents,
            has_heavy_strokes=has_heavy_strokes,
            is_mermaid_slop=is_mermaid_slop,
            anti_patterns=anti_patterns,
            editorial_suggestion=editorial_suggestion,
        )

