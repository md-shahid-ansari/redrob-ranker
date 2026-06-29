from datetime import datetime, date
from typing import Dict, Any, List, Tuple
from src.config import HONEYPOT

def detect_honeypot(candidate: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
    """
    Detect honeypot candidates based on multiple heuristics.
    Returns (is_honeypot, confidence, flags_list).
    """
    flags = []
    confidence = 0.0
    is_honeypot = False

    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])

    # 1. Salary inversion
    salary = signals.get("expected_salary_range_inr_lpa", {})
    if salary.get("min", 0) > salary.get("max", 0):
        flags.append("salary_inversion")
        confidence += 0.3

    # 2. Signup after last_active
    signup = signals.get("signup_date", "")
    last_active = signals.get("last_active_date", "")
    if signup and last_active and signup > last_active:
        flags.append("signup_after_last_active")
        confidence += 0.3

    # 3. Temporal impossibility: working before finishing school
    # Get earliest education end year
    edu_end_years = []
    for edu in education:
        end_year_str = edu.get("end_date", "")
        if end_year_str:
            try:
                # parse YYYY or YYYY-MM
                year = int(end_year_str[:4])
                edu_end_years.append(year)
            except:
                pass
    # Get earliest career start year
    career_start_years = []
    for job in career_history:
        start_str = job.get("start_date", "")
        if start_str:
            try:
                year = int(start_str[:4])
                career_start_years.append(year)
            except:
                pass
    # If any career start is before earliest education end? That's not necessarily impossible (could be part-time).
    # But if career start is before the candidate's typical graduation age (say 16), that's suspicious.
    # We'll check if career_start is < 2000 (or current_year - 16) but that's weak.
    # Instead, check if career_start is before education_end - 2? Actually we'll check if the career start is < 1990 (unlikely).
    # For simplicity, we'll only flag if any job start_year is < 1980 or > current_year+1.
    current_year = date.today().year
    for year in career_start_years:
        if year < 1980 or year > current_year + 1:
            flags.append("impossible_career_start_year")
            confidence += 0.4
            break

    # 4. Skill fraud: many expert skills with low endorsements and short duration
    expert_skills = []
    for skill in skills:
        prof = skill.get("proficiency", "").lower()
        endorsements = skill.get("endorsements_received", 0)
        duration = skill.get("duration_months", 0)
        if prof in ["expert", "advanced"] and endorsements < 3 and duration < 6:
            expert_skills.append(skill)
    if len(expert_skills) >= HONEYPOT.get("min_expert_skills", 5):
        flags.append("skill_fraud_many_expert_low_endorsement")
        confidence += 0.4

    # 5. Endorsement farming: high endorsements on beginner skill with short duration
    for skill in skills:
        prof = skill.get("proficiency", "").lower()
        endorsements = skill.get("endorsements_received", 0)
        duration = skill.get("duration_months", 0)
        if prof == "beginner" and endorsements > 50 and duration < 6:
            flags.append("endorsement_farming")
            confidence += 0.3
            break

    # 6. Profile coherence: summary vs career history mismatch (e.g., says "6 years as Backend Engineer" but all jobs are "Marketing Manager")
    # We'll check if summary contains keywords that don't match job titles.
    summary = profile.get("summary", "").lower()
    job_titles = [job.get("title", "").lower() for job in career_history]
    # If summary has "backend engineer" but no job title contains "backend" or "engineer", flag
    if "backend" in summary and not any("backend" in t or "engineer" in t for t in job_titles):
        flags.append("profile_summary_job_mismatch")
        confidence += 0.3
    # Similar for "data scientist", "machine learning", etc.
    ml_keywords = ["machine learning", "data scientist", "nlp", "ai", "deep learning"]
    for kw in ml_keywords:
        if kw in summary and not any(kw in t for t in job_titles):
            flags.append(f"summary_{kw}_mismatch")
            confidence += 0.2
            break

    # 7. Overlapping job tenures that are impossible (same company, same title)
    # Simple check: if any two jobs have same company and overlapping dates
    for i in range(len(career_history)):
        for j in range(i+1, len(career_history)):
            job1 = career_history[i]
            job2 = career_history[j]
            if job1.get("company", "") == job2.get("company", ""):
                # Check if date ranges overlap
                try:
                    start1 = datetime.strptime(job1["start_date"], "%Y-%m-%d")
                    end1 = datetime.strptime(job1["end_date"], "%Y-%m-%d") if job1.get("end_date") and job1["end_date"].lower() != "present" else datetime.now()
                    start2 = datetime.strptime(job2["start_date"], "%Y-%m-%d")
                    end2 = datetime.strptime(job2["end_date"], "%Y-%m-%d") if job2.get("end_date") and job2["end_date"].lower() != "present" else datetime.now()
                    if max(start1, start2) <= min(end1, end2):
                        flags.append("overlapping_jobs_same_company")
                        confidence += 0.4
                        break
                except:
                    pass
        else:
            continue
        break

    # 8. Age impossibility: career_start implies age < 16 (if we had age) - skip for now.

    # 9. Salary min/max values unrealistic? Not needed.

    # Determine if honeypot
    if confidence >= 0.5:
        is_honeypot = True

    # Cap confidence at 1.0
    confidence = min(1.0, confidence)

    return is_honeypot, confidence, flags

if __name__ == "__main__":
    from src.loader import load_candidates_stream
    sample = next(load_candidates_stream())
    is_hp, conf, flags = detect_honeypot(sample)
    print(f"Honeypot: {is_hp}, confidence: {conf:.2f}, flags: {flags}")