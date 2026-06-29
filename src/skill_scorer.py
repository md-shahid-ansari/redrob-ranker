from typing import Dict, Any, List, Set
from src.config import JD_REQUIRED_SKILLS, JD_NICE_TO_HAVE, SKILL_SUB_WEIGHTS, RED_FLAG_SKILLS, MIN_ENDORSEMENTS_FOR_TRUST, MIN_DURATION_MONTHS_FOR_TRUST, ASSESSMENT_THRESHOLD_GOOD

def get_skill_trust( skill: Dict[str, Any]) -> float:
    """
    Compute a trust multiplier (0.2–1.0) based on endorsements, duration, and assessment score.
    """
    endorsements = skill.get("endorsements_received", 0)
    duration_months = skill.get("duration_months", 0)
    assessment_score = skill.get("assessment_score", 0)  # 0-100

    # Base trust starts at 0.5
    trust = 0.5

    # Endorsements boost
    if endorsements >= MIN_ENDORSEMENTS_FOR_TRUST:
        trust += min(0.4, endorsements / 50)  # cap at +0.4 for 20+ endorsements
    else:
        trust -= 0.2  # penalty for low endorsements

    # Duration boost
    if duration_months >= MIN_DURATION_MONTHS_FOR_TRUST:
        trust += min(0.3, duration_months / 48)  # cap at +0.3 for 48+ months
    else:
        trust -= 0.1

    # Assessment score boost
    if assessment_score >= ASSESSMENT_THRESHOLD_GOOD:
        trust += 0.3
    elif assessment_score > 0:
        trust += 0.1

    # Clamp to [0.2, 1.0]
    return max(0.2, min(1.0, trust))

def skill_score(candidate: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute skill sub‑scores and overall skill score.
    Returns dict with keys: total, must_have_coverage, trust_adjustment, nice_to_have_bonus, red_flag_penalty.
    """
    skills = candidate.get("skills", [])

    # Build a map of skill name -> skill dict
    skill_map = {s.get("name", "").lower(): s for s in skills}

    # ------------------- Must‑have coverage -------------------
    required = set(JD_REQUIRED_SKILLS)
    must_have_matches = []
    for req_skill in required:
        if req_skill.lower() in skill_map:
            # Found skill
            skill_info = skill_map[req_skill.lower()]
            # Check proficiency: beginner, intermediate, advanced, expert -> map to 0.2, 0.5, 0.8, 1.0
            prof = skill_info.get("proficiency", "beginner").lower()
            prof_score = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}.get(prof, 0.3)
            # trust adjustment applied later; for coverage, just count presence with proficiency weight
            must_have_matches.append(prof_score)
        else:
            # Check if skill appears in summary or job descriptions (semantic later; for now just keyword)
            # We'll handle semantic similarity in ranker, so here we just do keyword match.
            pass

    # Coverage is proportion of required skills found, weighted by proficiency (but we'll use raw presence for now)
    if required:
        # simple binary: count how many are present
        found_count = sum(1 for req in required if req.lower() in skill_map)
        raw_coverage = found_count / len(required)
    else:
        raw_coverage = 1.0

    # ------------------- Trust adjustment -------------------
    # For each matched required skill, compute trust multiplier and multiply with proficiency
    trust_adjustment = 0.0
    trust_matches = 0
    for req_skill in required:
        if req_skill.lower() in skill_map:
            skill_info = skill_map[req_skill.lower()]
            trust = get_skill_trust(skill_info)
            prof = skill_info.get("proficiency", "beginner").lower()
            prof_score = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}.get(prof, 0.3)
            trust_adjustment += trust * prof_score
            trust_matches += 1

    if trust_matches > 0:
        trust_adjustment = trust_adjustment / trust_matches
    else:
        trust_adjustment = 0.0

    # ------------------- Nice‑to‑have bonus -------------------
    nice_to_have = set(JD_NICE_TO_HAVE)
    nice_found = sum(1 for skill in nice_to_have if skill.lower() in skill_map)
    nice_bonus = nice_found / len(nice_to_have) if nice_to_have else 0.0

    # ------------------- Red flag penalty -------------------
    # Penalize if candidate has expertise in RED_FLAG_SKILLS but not in NLP/retrieval etc.
    # We'll check if they have any red flag skill at advanced/expert level
    has_red_flag = False
    for skill_name in RED_FLAG_SKILLS:
        if skill_name.lower() in skill_map:
            skill_info = skill_map[skill_name.lower()]
            prof = skill_info.get("proficiency", "beginner").lower()
            if prof in ["advanced", "expert"]:
                has_red_flag = True
                break
    # Also check if they have any NLP-related skill (to offset)
    has_nlp = any("nlp" in s.lower() or "retrieval" in s.lower() or "embedding" in s.lower() for s in skill_map.keys())
    if has_red_flag and not has_nlp:
        penalty = 0.3  # reduce score by 0.3
    else:
        penalty = 0.0

    # ------------------- Weighted total -------------------
    total = (
        SKILL_SUB_WEIGHTS["must_have_coverage"] * raw_coverage +
        SKILL_SUB_WEIGHTS["trust_adjustment"] * trust_adjustment +
        SKILL_SUB_WEIGHTS["nice_to_have_bonus"] * nice_bonus
    ) - (SKILL_SUB_WEIGHTS["red_flag_penalty"] * penalty)

    # Clamp to [0, 1]
    total = max(0.0, min(1.0, total))

    return {
        "total": total,
        "must_have_coverage": raw_coverage,
        "trust_adjustment": trust_adjustment,
        "nice_to_have_bonus": nice_bonus,
        "red_flag_penalty": penalty,
    }

if __name__ == "__main__":
    # Quick test
    from src.loader import load_candidates_stream
    sample = next(load_candidates_stream())
    scores = skill_score(sample)
    print("Skill scores:", scores)