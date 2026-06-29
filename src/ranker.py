from typing import Dict, Any, Tuple
from src.config import WEIGHTS, LOCATION_WEIGHTS
from src.career_scorer import career_score
from src.skill_scorer import skill_score
from src.behavioral_scorer import behavioral_score
from src.honeypot_detector import detect_honeypot

def location_score(candidate: Dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    city = profile.get("city", "").lower().strip()
    for loc, weight in LOCATION_WEIGHTS.items():
        if loc in city:
            return weight
    return 0.3

def compute_final_score(candidate: Dict[str, Any], semantic_sim: float) -> Tuple[float, Dict[str, Any], bool, float, list]:
    """
    Returns: (final_score, all_scores_dict, is_honeypot, confidence, flags)
    """
    career = career_score(candidate)
    skill = skill_score(candidate)
    behavioral = behavioral_score(candidate)
    loc = location_score(candidate)

    is_honeypot, confidence, flags = detect_honeypot(candidate)

    final = (
        WEIGHTS["semantic"] * semantic_sim +
        WEIGHTS["career"] * career["total"] +
        WEIGHTS["skill"] * skill["total"] +
        WEIGHTS["behavioral"] * behavioral["total"] +
        WEIGHTS["location"] * loc
    )

    if is_honeypot:
        final = min(final, 0.05)

    final = max(0.0, min(1.0, final))

    all_scores = {
        "semantic": semantic_sim,
        "career": career["total"],
        "skill": skill["total"],
        "behavioral": behavioral["total"],
        "location": loc,
        "final": final,
        "career_details": career,
        "skill_details": skill,
        "behavioral_details": behavioral,
    }
    return final, all_scores, is_honeypot, confidence, flags