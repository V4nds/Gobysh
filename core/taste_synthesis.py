import dataclasses
from typing import List, Dict

@dataclasses.dataclass
class TasteEvaluation:
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


class TasteSynthesisEngine:
    """
    Goby's Right Brain: The Artist.
    Evaluates UI/UX code against modern design aesthetics to minimize slop and noise.
    Uses multi-dimensional evaluation: Spatial (Pro Max), Motion (GSAP), Visual (Layering), and Genjutsu (WebGL).
    """

    DIMENSIONS = {
        "spatial": ["flex", "grid", "clamp", "calc", "bento", "auto-layout", "gap-"],
        "motion": ["transition", "transform", "hover:", "gsap", "motion", "animate", "stagger"],
        "visual": ["opacity", "shadow", "gradient", "backdrop", "backdrop-filter", "var(--", "glass", "blur"],
        "genjutsu": ["three", "canvas", "webgl", "particles", "lottie", "orbit"]
    }

    @classmethod
    def evaluate(cls, code: str) -> TasteEvaluation:
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

        return TasteEvaluation(
            is_slop=is_slop,
            spatial_score=scores["spatial"],
            motion_score=scores["motion"],
            visual_score=scores["visual"],
            genjutsu_score=scores["genjutsu"],
            total_score=total_score,
            detected_keywords=detected_keywords,
            bypass_suggestion=bypass_suggestion
        )
