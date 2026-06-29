from datetime import datetime
from typing import Dict, Any
from src.config import SERVICES_COMPANIES, PRODUCT_COMPANIES, ML_TITLE_KEYWORDS, CAREER_SUB_WEIGHTS

# Simple title level mapping for trajectory scoring
TITLE_LEVELS = {
    "intern": 0,
    "trainee": 1,
    "engineer": 2,
    "developer": 2,
    "analyst": 2,
    "associate": 3,
    "senior": 4,
    "lead": 5,
    "principal": 6,
    "manager": 5,
    "director": 7,
    "vp": 8,
    "cto": 9,
    "architect": 6,
}

def parse_date(date_str: str) -> datetime:
    """Convert 'YYYY-MM-DD' to datetime. If missing day, assume first of month."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # Try with just year-month
        return datetime.strptime(date_str, "%Y-%m")

def get_company_type(company_name: str) -> str:
    """Return 'product', 'services', or 'unknown'."""
    company_lower = company_name.lower().strip()
    if company_lower in SERVICES_COMPANIES:
        return "services"
    if company_lower in PRODUCT_COMPANIES:
        return "product"
    # Heuristic: if company name contains 'tech' or 'solutions' but not in product list, treat as unknown
    return "unknown"

def is_ml_title(title: str) -> bool:
    """Check if title contains ML-related keywords."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in ML_TITLE_KEYWORDS)

def career_score(candidate: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute career sub‑scores and overall score.
    Returns dict with keys: total, product_company, ml_role, yoe_fit,
                            tenure_stability, trajectory, recency
    """
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    current_title = profile.get("current_title", "")
    current_company = profile.get("current_company", "")
    industry = profile.get("current_industry", "")
    yoe = profile.get("years_of_experience", 0.0)

    # ---------- Product company score ----------
    # We'll look at all companies in career history, but give more weight to current and recent.
    # For simplicity, we'll compute average company type score over all jobs.
    company_scores = []
    for job in career_history:
        company = job.get("company", "")
        ctype = get_company_type(company)
        if ctype == "product":
            company_scores.append(1.0)
        elif ctype == "services":
            company_scores.append(0.0)
        else:
            # unknown: 0.3 neutral
            company_scores.append(0.3)
    if not company_scores:
        # fallback: use current company if no history
        ctype = get_company_type(current_company)
        if ctype == "product":
            company_scores.append(1.0)
        elif ctype == "services":
            company_scores.append(0.0)
        else:
            company_scores.append(0.3)
    # Weight more recent jobs higher? For now simple average.
    product_company_score = sum(company_scores) / len(company_scores)

    # ---------- ML role score ----------
    # Check current title and summary, also job titles in career_history.
    title_score = 1.0 if is_ml_title(current_title) else 0.0
    # Also check summary
    summary = profile.get("summary", "")
    summary_ml = 1.0 if any(kw in summary.lower() for kw in ML_TITLE_KEYWORDS) else 0.0
    # Check career history titles
    history_ml = []
    for job in career_history:
        job_title = job.get("title", "")
        history_ml.append(1.0 if is_ml_title(job_title) else 0.0)
    if history_ml:
        hist_avg = sum(history_ml) / len(history_ml)
    else:
        hist_avg = 0.0
    # Combine: current title most important, then summary, then history.
    ml_role_score = 0.5 * title_score + 0.3 * summary_ml + 0.2 * hist_avg

    # ---------- YoE fit score ----------
    ideal_min, ideal_max = 5, 9  # from config maybe
    if ideal_min <= yoe <= ideal_max:
        yoe_fit = 1.0
    elif yoe < ideal_min:
        # linear drop from 1 at ideal_min to 0 at 0
        yoe_fit = max(0.0, yoe / ideal_min)
    else:
        # yoe > ideal_max, linear drop to 0 at 15
        yoe_fit = max(0.0, 1.0 - (yoe - ideal_max) / (15 - ideal_max))
    yoe_fit = min(1.0, yoe_fit)

    # ---------- Tenure stability score ----------
    # Compute average months per job.
    durations = []
    for job in career_history:
        start = job.get("start_date")
        end = job.get("end_date")
        if not start:
            continue
        try:
            start_dt = parse_date(start)
        except:
            continue
        if end and end.strip() and end.lower() != "present":
            try:
                end_dt = parse_date(end)
                months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            except:
                continue
        else:
            # current job: use today
            today = datetime.now()
            months = (today.year - start_dt.year) * 12 + (today.month - start_dt.month)
        if months > 0:
            durations.append(months)
    if durations:
        avg_tenure = sum(durations) / len(durations)
        # Ideal: 18-48 months (1.5 - 4 years)
        if 18 <= avg_tenure <= 48:
            stability = 1.0
        elif avg_tenure < 12:
            stability = 0.2  # job hopper
        elif avg_tenure < 18:
            stability = 0.6
        elif avg_tenure > 48:
            stability = 0.8  # too long might indicate stagnation but not penalised heavily
        else:
            stability = 0.5
    else:
        stability = 0.5  # no data

    # ---------- Trajectory score ----------
    # Examine progression of titles over time.
    # We'll compute a simple trend: map titles to levels, then check if level increases.
    if len(career_history) >= 2:
        levels = []
        for job in career_history:
            title = job.get("title", "")
            # find level
            level = 0
            for key, val in TITLE_LEVELS.items():
                if key in title.lower():
                    level = max(level, val)
            # also check if title contains "senior", "lead" etc.
            if "senior" in title.lower() or "lead" in title.lower():
                level = max(level, 4)
            if "principal" in title.lower():
                level = max(level, 6)
            levels.append(level)
        # check if levels generally increase over time (assuming chronologically sorted)
        # We'll compute a simple linear regression slope or just check last vs first.
        if len(levels) >= 2:
            # take first job and last job (most recent)
            first_level = levels[0]
            last_level = levels[-1]
            if last_level > first_level:
                trajectory = 1.0
            elif last_level == first_level:
                trajectory = 0.5
            else:
                trajectory = 0.2
        else:
            trajectory = 0.5
    else:
        trajectory = 0.5

    # ---------- Recency score ----------
    # Is the current role ML? Already have current title ML score; we can use that directly.
    recency = title_score  # 1 if current title is ML, else 0

    # ---------- Weighted total ----------
    total = (
        CAREER_SUB_WEIGHTS["product_company"] * product_company_score +
        CAREER_SUB_WEIGHTS["ml_role"] * ml_role_score +
        CAREER_SUB_WEIGHTS["yoe_fit"] * yoe_fit +
        CAREER_SUB_WEIGHTS["tenure_stability"] * stability +
        CAREER_SUB_WEIGHTS["trajectory"] * trajectory +
        CAREER_SUB_WEIGHTS["recency"] * recency
    )

    return {
        "total": total,
        "product_company": product_company_score,
        "ml_role": ml_role_score,
        "yoe_fit": yoe_fit,
        "tenure_stability": stability,
        "trajectory": trajectory,
        "recency": recency,
    }

if __name__ == "__main__":
    # Quick test using a sample candidate (load first candidate)
    from src.loader import load_candidates_stream
    sample = next(load_candidates_stream())
    scores = career_score(sample)
    print("Career scores:", scores)