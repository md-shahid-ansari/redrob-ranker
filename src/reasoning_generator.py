from typing import Dict, Any

def generate_reasoning(candidate: Dict[str, Any], scores: Dict[str, float], rank: int, is_honeypot: bool) -> str:
    """
    Generate human-readable reasoning for the candidate's rank.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_details = scores.get("career_details", {})
    skill_details = scores.get("skill_details", {})
    behavioral_details = scores.get("behavioral_details", {})

    # Collect positive signals
    positives = []
    concerns = []

    # Career
    if career_details.get("product_company", 0) >= 0.7:
        positives.append("strong product-company background")
    elif career_details.get("product_company", 0) < 0.3:
        concerns.append("predominantly services-company experience")

    if career_details.get("ml_role", 0) >= 0.7:
        positives.append("current role is ML/AI-focused")
    elif career_details.get("ml_role", 0) < 0.3:
        concerns.append("limited ML/AI role experience")

    yoe = profile.get("years_of_experience", 0)
    if 5 <= yoe <= 9:
        positives.append(f"ideal YoE ({yoe:.1f} years)")
    elif yoe < 5:
        concerns.append(f"less than ideal YoE ({yoe:.1f} years)")
    elif yoe > 9:
        concerns.append(f"above ideal YoE ({yoe:.1f} years)")

    # Skill
    must_have = skill_details.get("must_have_coverage", 0)
    if must_have >= 0.5:
        positives.append(f"good coverage of required skills ({must_have:.0%})")
    else:
        concerns.append(f"low coverage of required skills ({must_have:.0%})")

    trust = skill_details.get("trust_adjustment", 0)
    if trust >= 0.7:
        positives.append("high trust in skill endorsements/assessments")
    elif trust < 0.3:
        concerns.append("low trust signals for skills (few endorsements/short durations)")

    # Behavioral
    availability = behavioral_details.get("availability", 0)
    if availability >= 0.7:
        positives.append("high availability (active, open to work, short notice)")
    else:
        concerns.append("lower availability (inactive or long notice)")

    engagement = behavioral_details.get("engagement", 0)
    if engagement >= 0.7:
        positives.append("high platform engagement (response rate, etc.)")

    # Location
    loc_score = scores.get("location", 0)
    if loc_score >= 0.8:
        positives.append("preferred location")
    elif loc_score < 0.3:
        concerns.append("not in preferred location")

    # Honeypot
    if is_honeypot:
        concerns.append("potential profile inconsistencies detected")

    # Construct reasoning
    reason_parts = []
    if positives:
        reason_parts.append("Strengths: " + "; ".join(positives[:3]))
    if concerns:
        reason_parts.append("Concerns: " + "; ".join(concerns[:3]))

    # Add a summary sentence about the role
    current_title = profile.get("current_title", "Unknown")
    company = profile.get("current_company", "Unknown")
    reason_parts.append(f"Currently {current_title} at {company}")

    # Tone based on rank
    if rank <= 10:
        intro = "Top-tier candidate. "
    elif rank <= 30:
        intro = "Strong candidate. "
    elif rank <= 60:
        intro = "Good candidate. "
    else:
        intro = "Candidate. "

    full_reason = intro + " ".join(reason_parts)
    # Truncate if too long
    if len(full_reason) > 200:
        full_reason = full_reason[:197] + "..."

    return full_reason