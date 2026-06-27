"""
EDA — Redrob Dataset Exploration
Run: python notebooks/eda.py
Prints key statistics we need to make scoring decisions.
"""

import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, date
import statistics

CANDIDATES_PATH = "data/candidates.jsonl.gz"
SAMPLE_PATH = "data/sample_candidates.json"

def load_sample():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_all(limit=None):
    candidates = []
    with gzip.open(CANDIDATES_PATH, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            if line.strip():
                candidates.append(json.loads(line))
    return candidates

def analyze(candidates):
    print(f"\n{'='*60}")
    print(f"DATASET: {len(candidates)} candidates")
    print(f"{'='*60}")

    # --- YoE distribution ---
    yoe_list = [c["profile"]["years_of_experience"] for c in candidates]
    print(f"\n--- Years of Experience ---")
    print(f"  Min: {min(yoe_list):.1f}")
    print(f"  Max: {max(yoe_list):.1f}")
    print(f"  Mean: {statistics.mean(yoe_list):.1f}")
    print(f"  Median: {statistics.median(yoe_list):.1f}")
    buckets = {"0-2": 0, "3-4": 0, "5-9 (target)": 0, "10-14": 0, "15+": 0}
    for y in yoe_list:
        if y <= 2: buckets["0-2"] += 1
        elif y <= 4: buckets["3-4"] += 1
        elif y <= 9: buckets["5-9 (target)"] += 1
        elif y <= 14: buckets["10-14"] += 1
        else: buckets["15+"] += 1
    for k, v in buckets.items():
        print(f"  {k}: {v} ({v/len(candidates)*100:.1f}%)")

    # --- Current titles ---
    print(f"\n--- Top 20 Current Titles ---")
    titles = Counter(c["profile"]["current_title"] for c in candidates)
    for title, count in titles.most_common(20):
        print(f"  {count:5d}  {title}")

    # --- Industries ---
    print(f"\n--- Top 15 Current Industries ---")
    industries = Counter(c["profile"]["current_industry"] for c in candidates)
    for ind, count in industries.most_common(15):
        print(f"  {count:5d}  {ind}")

    # --- Companies (current) ---
    print(f"\n--- Top 20 Current Companies ---")
    companies = Counter(c["profile"]["current_company"] for c in candidates)
    for co, count in companies.most_common(20):
        print(f"  {count:5d}  {co}")

    # --- Countries ---
    print(f"\n--- Countries ---")
    countries = Counter(c["profile"]["country"] for c in candidates)
    for co, count in countries.most_common(10):
        print(f"  {count:5d}  {co}")

    # --- Skills ---
    print(f"\n--- Top 30 Skills (by frequency) ---")
    skill_counter = Counter()
    proficiency_map = defaultdict(list)
    for c in candidates:
        for s in c.get("skills", []):
            skill_counter[s["name"]] += 1
            proficiency_map[s["name"]].append(s["proficiency"])
    for skill, count in skill_counter.most_common(30):
        print(f"  {count:5d}  {skill}")

    # --- AI/ML relevant skills ---
    ml_skills = [
        "embeddings", "vector search", "FAISS", "Pinecone", "Weaviate", "Qdrant",
        "Milvus", "Elasticsearch", "OpenSearch", "sentence-transformers",
        "Hugging Face Transformers", "Fine-tuning LLMs", "LoRA", "PEFT",
        "NLP", "Information Retrieval", "BM25", "LangChain", "MLOps", "MLflow",
        "Recommendation Systems", "Feature Engineering", "PyTorch", "TensorFlow",
        "scikit-learn", "XGBoost", "LightGBM", "Reinforcement Learning",
        "Deep Learning", "Machine Learning", "Haystack", "Sentence Transformers",
        "Embeddings", "Vector Search", "Prompt Engineering", "RAG", "Kubeflow"
    ]
    print(f"\n--- ML/AI Skill Coverage ---")
    for skill in ml_skills:
        count = skill_counter.get(skill, 0)
        if count > 0:
            print(f"  {count:5d}  {skill}")

    # --- Open to work ---
    otw = sum(1 for c in candidates if c["redrob_signals"]["open_to_work_flag"])
    print(f"\n--- Availability ---")
    print(f"  Open to work: {otw} ({otw/len(candidates)*100:.1f}%)")

    # --- Last active date distribution ---
    today = date.today()
    active_buckets = {"<30d": 0, "30-90d": 0, "90-180d": 0, "180d+": 0}
    for c in candidates:
        last_active = datetime.strptime(
            c["redrob_signals"]["last_active_date"], "%Y-%m-%d"
        ).date()
        days_ago = (today - last_active).days
        if days_ago < 30: active_buckets["<30d"] += 1
        elif days_ago < 90: active_buckets["30-90d"] += 1
        elif days_ago < 180: active_buckets["90-180d"] += 1
        else: active_buckets["180d+"] += 1
    print(f"\n--- Last Active ---")
    for k, v in active_buckets.items():
        print(f"  {k}: {v} ({v/len(candidates)*100:.1f}%)")

    # --- Notice period ---
    notice_list = [c["redrob_signals"]["notice_period_days"] for c in candidates]
    notice_buckets = {"0-30d": 0, "31-60d": 0, "61-90d": 0, "90+d": 0}
    for n in notice_list:
        if n <= 30: notice_buckets["0-30d"] += 1
        elif n <= 60: notice_buckets["31-60d"] += 1
        elif n <= 90: notice_buckets["61-90d"] += 1
        else: notice_buckets["90+d"] += 1
    print(f"\n--- Notice Period ---")
    for k, v in notice_buckets.items():
        print(f"  {k}: {v} ({v/len(candidates)*100:.1f}%)")

    # --- GitHub activity ---
    has_github = sum(
        1 for c in candidates
        if c["redrob_signals"]["github_activity_score"] != -1
    )
    print(f"\n--- GitHub ---")
    print(f"  Has GitHub linked: {has_github} ({has_github/len(candidates)*100:.1f}%)")

    # --- Education tiers ---
    print(f"\n--- Education Tiers ---")
    tier_counter = Counter()
    for c in candidates:
        tiers = [e.get("tier", "unknown") for e in c.get("education", [])]
        best = "unknown"
        for t in ["tier_1", "tier_2", "tier_3", "tier_4", "unknown"]:
            if t in tiers:
                best = t
                break
        tier_counter[best] += 1
    for tier, count in sorted(tier_counter.items()):
        print(f"  {tier}: {count} ({count/len(candidates)*100:.1f}%)")

    # --- Recruiter response rate ---
    rr_list = [c["redrob_signals"]["recruiter_response_rate"] for c in candidates]
    print(f"\n--- Recruiter Response Rate ---")
    print(f"  Mean: {statistics.mean(rr_list):.2f}")
    print(f"  Median: {statistics.median(rr_list):.2f}")
    high_rr = sum(1 for r in rr_list if r >= 0.5)
    print(f"  >= 0.5: {high_rr} ({high_rr/len(candidates)*100:.1f}%)")

    # --- Skill assessment scores ---
    has_assessment = sum(
        1 for c in candidates
        if c["redrob_signals"]["skill_assessment_scores"]
    )
    print(f"\n--- Skill Assessments ---")
    print(f"  Has at least 1 assessment: {has_assessment} ({has_assessment/len(candidates)*100:.1f}%)")

    # --- Honeypot signals: salary inversion ---
    salary_inverted = sum(
        1 for c in candidates
        if (c["redrob_signals"]["expected_salary_range_inr_lpa"]["min"] >
            c["redrob_signals"]["expected_salary_range_inr_lpa"]["max"])
    )
    print(f"\n--- Potential Honeypot Signals ---")
    print(f"  Salary inverted (min > max): {salary_inverted}")

    # signup after last_active
    date_anomaly = sum(
        1 for c in candidates
        if c["redrob_signals"]["signup_date"] > c["redrob_signals"]["last_active_date"]
    )
    print(f"  Signup after last_active: {date_anomaly}")

    # --- Sample of likely-good candidates (heuristic) ---
    print(f"\n--- Sample Strong Candidates (heuristic filter) ---")
    strong = []
    ml_title_keywords = [
        "ml", "ai", "machine learning", "nlp", "data scientist",
        "search", "recommendation", "ranking", "retrieval", "applied"
    ]
    for c in candidates:
        title = c["profile"]["current_title"].lower()
        summary = c["profile"]["summary"].lower()
        yoe = c["profile"]["years_of_experience"]
        industry = c["profile"]["current_industry"]

        is_ml_title = any(kw in title for kw in ml_title_keywords)
        is_ml_summary = any(kw in summary for kw in ml_title_keywords)
        yoe_ok = 4 <= yoe <= 12
        not_services_only = industry not in ["IT Services"]  # rough

        if (is_ml_title or is_ml_summary) and yoe_ok:
            strong.append(c)

    print(f"  Found {len(strong)} potentially strong candidates")
    for c in strong[:10]:
        sig = c["redrob_signals"]
        print(f"\n  {c['candidate_id']} | {c['profile']['anonymized_name']}")
        print(f"    Title: {c['profile']['current_title']}")
        print(f"    YoE: {c['profile']['years_of_experience']}")
        print(f"    Company: {c['profile']['current_company']} ({c['profile']['current_industry']})")
        print(f"    Last active: {sig['last_active_date']} | OTW: {sig['open_to_work_flag']}")
        print(f"    Notice: {sig['notice_period_days']}d | Response rate: {sig['recruiter_response_rate']:.0%}")
        top_skills = [
            s["name"] for s in c.get("skills", [])
            if s["proficiency"] in ("advanced", "expert")
        ]
        print(f"    Top skills: {', '.join(top_skills[:5]) if top_skills else 'none'}")


if __name__ == "__main__":
    print("Loading sample (50 candidates)...")
    sample = load_sample()
    print(f"Sample loaded: {len(sample)} candidates")
    analyze(sample)

    print("\n\nLoading FULL dataset (this takes ~30 seconds)...")
    all_candidates = load_all()
    analyze(all_candidates)