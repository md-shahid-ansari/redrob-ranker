from datetime import datetime, date
from typing import Dict, Any, List, Union
from src.config import BEHAVIORAL_SUB_WEIGHTS, NOTICE_PREFERRED, LAST_ACTIVE_PREFERRED

def parse_assessment_scores(assessments: Union[List, Any]) -> List[float]:
    """Convert assessment scores to floats, ignoring non-numeric."""
    if not isinstance(assessments, list):
        return []
    result = []
    for val in assessments:
        try:
            result.append(float(val))
        except (ValueError, TypeError):
            pass
    return result

def behavioral_score(candidate: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute behavioral sub‑scores and overall behavioral score.
    Returns dict with keys: total, availability, engagement, credibility, market_demand, reliability.
    """
    signals = candidate.get("redrob_signals", {})

    # ---------- Availability ----------
    last_active_str = signals.get("last_active_date", "")
    try:
        last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        days_inactive = (date.today() - last_active).days
    except:
        days_inactive = 180  # conservative

    if days_inactive < LAST_ACTIVE_PREFERRED:
        last_active_score = 1.0
    elif days_inactive < 90:
        last_active_score = 0.7
    elif days_inactive < 180:
        last_active_score = 0.4
    else:
        last_active_score = 0.2

    otw = 1.0 if signals.get("open_to_work_flag", False) else 0.0

    notice = signals.get("notice_period_days", 90)
    if notice <= NOTICE_PREFERRED:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.7
    elif notice <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.1

    availability = 0.5 * last_active_score + 0.2 * otw + 0.3 * notice_score

    # ---------- Engagement ----------
    response_rate = signals.get("recruiter_response_rate", 0.0)
    avg_response_time = signals.get("avg_response_time_hours", 999)
    apps_30d = signals.get("applications_submitted_30d", 0)

    if response_rate >= 0.8:
        resp_score = 1.0
    elif response_rate >= 0.5:
        resp_score = 0.7
    elif response_rate >= 0.2:
        resp_score = 0.4
    else:
        resp_score = 0.2

    if avg_response_time < 24:
        time_score = 1.0
    elif avg_response_time < 48:
        time_score = 0.7
    elif avg_response_time < 168:
        time_score = 0.4
    else:
        time_score = 0.1

    if 1 <= apps_30d <= 5:
        apps_score = 1.0
    elif apps_30d <= 10:
        apps_score = 0.7
    elif apps_30d > 10:
        apps_score = 0.4
    else:
        apps_score = 0.5

    engagement = 0.4 * resp_score + 0.3 * time_score + 0.3 * apps_score

    # ---------- Credibility ----------
    verified_email = signals.get("verified_email", False)
    verified_phone = signals.get("verified_phone", False)
    completeness = signals.get("profile_completeness_score", 0.0)
    github_score = signals.get("github_activity_score", -1)

    if verified_email and verified_phone:
        verify_score = 1.0
    elif verified_email or verified_phone:
        verify_score = 0.5
    else:
        verify_score = 0.2

    if completeness >= 0.8:
        comp_score = 1.0
    elif completeness >= 0.6:
        comp_score = 0.7
    else:
        comp_score = 0.3

    if github_score >= 0.5:
        github_score_norm = 1.0
    elif github_score >= 0:
        github_score_norm = 0.5
    else:
        github_score_norm = 0.0

    credibility = 0.4 * verify_score + 0.3 * comp_score + 0.3 * github_score_norm

    # ---------- Market Demand ----------
    saved = signals.get("saved_by_recruiters_30d", 0)
    search_appear = signals.get("search_appearance_30d", 0)
    assessments = signals.get("skill_assessment_scores", [])

    # saved: >5 is good
    if saved >= 10:
        saved_score = 1.0
    elif saved >= 5:
        saved_score = 0.7
    elif saved >= 1:
        saved_score = 0.4
    else:
        saved_score = 0.1

    if search_appear >= 10:
        search_score = 1.0
    elif search_appear >= 5:
        search_score = 0.7
    elif search_appear >= 1:
        search_score = 0.4
    else:
        search_score = 0.1

    # assessments: if any >60, boost
    if assessments:
        # Ensure numeric values
        numeric_scores = []
        for s in assessments:
            try:
                numeric_scores.append(float(s))
            except (ValueError, TypeError):
                pass
        if numeric_scores:
            avg_assessment = sum(numeric_scores) / len(numeric_scores)
            if avg_assessment >= 70:
                assess_score = 1.0
            elif avg_assessment >= 50:
                assess_score = 0.6
            else:
                assess_score = 0.3
        else:
            assess_score = 0.0
    else:
        assess_score = 0.0

    market_demand = 0.4 * saved_score + 0.3 * search_score + 0.3 * assess_score

    # ---------- Reliability ----------
    interview_rate = signals.get("interview_completion_rate", 0.0)
    offer_acceptance = signals.get("offer_acceptance_rate", -1)

    if interview_rate >= 0.8:
        interview_score = 1.0
    elif interview_rate >= 0.5:
        interview_score = 0.6
    elif interview_rate >= 0.3:
        interview_score = 0.3
    else:
        interview_score = 0.1

    if offer_acceptance >= 0:
        if 0.4 <= offer_acceptance <= 0.7:
            offer_score = 1.0
        elif 0.2 <= offer_acceptance < 0.4:
            offer_score = 0.6
        elif 0.7 < offer_acceptance <= 0.9:
            offer_score = 0.6
        else:
            offer_score = 0.3
    else:
        offer_score = 0.5

    reliability = 0.6 * interview_score + 0.4 * offer_score

    # ---------- Weighted total ----------
    total = (
        BEHAVIORAL_SUB_WEIGHTS["availability"] * availability +
        BEHAVIORAL_SUB_WEIGHTS["engagement"] * engagement +
        BEHAVIORAL_SUB_WEIGHTS["credibility"] * credibility +
        BEHAVIORAL_SUB_WEIGHTS["market_demand"] * market_demand +
        BEHAVIORAL_SUB_WEIGHTS["reliability"] * reliability
    )
    total = max(0.0, min(1.0, total))

    return {
        "total": total,
        "availability": availability,
        "engagement": engagement,
        "credibility": credibility,
        "market_demand": market_demand,
        "reliability": reliability,
    }

if __name__ == "__main__":
    from src.loader import load_candidates_stream
    sample = next(load_candidates_stream())
    scores = behavioral_score(sample)
    print("Behavioral scores:", scores)