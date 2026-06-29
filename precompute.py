"""
Run this once to generate embeddings for all candidates and the JD.
Saves:
  - data/precomputed/candidate_embeddings.npy (float32, shape N x dim)
  - data/precomputed/candidate_ids.json (list of candidate IDs in same order)
  - data/precomputed/jd_embedding.npy (float32, shape dim)
"""

import json
import numpy as np
from pathlib import Path

from src.loader import load_candidates_stream
from src.embedder import Embedder
from src.jd_parser import load_jd_text

# Output paths
PRECOMPUTED_DIR = Path("data/precomputed")
PRECOMPUTED_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_PATH = PRECOMPUTED_DIR / "candidate_embeddings.npy"
IDS_PATH = PRECOMPUTED_DIR / "candidate_ids.json"
JD_EMBEDDING_PATH = PRECOMPUTED_DIR / "jd_embedding.npy"

BATCH_SIZE = 256  # adjust based on RAM

def build_candidate_text(candidate):
    """
    Build a textual representation for a candidate.
    We combine: headline (current title), summary, skills (with proficiency/endorsements),
    and career history descriptions.
    """
    profile = candidate["profile"]
    parts = []

    # Current title
    title = profile.get("current_title", "")
    if title:
        parts.append(f"Title: {title}")

    # Summary
    summary = profile.get("summary", "")
    if summary:
        parts.append(f"Summary: {summary}")

    # Skills – include name, proficiency, and number of endorsements (if present)
    skill_texts = []
    for skill in candidate.get("skills", []):
        name = skill.get("name", "")
        prof = skill.get("proficiency", "")
        endorsements = skill.get("endorsements", 0)
        # Only include if we have a name
        if name:
            # Add context: "skill_name (proficiency, endorsements)"
            skill_texts.append(f"{name} ({prof}, {endorsements} endorsements)")
    if skill_texts:
        parts.append("Skills: " + ", ".join(skill_texts))

    # Career history – each job: title, company, industry, description
    career_texts = []
    for job in candidate.get("career_history", []):
        job_title = job.get("title", "")
        company = job.get("company", "")
        industry = job.get("industry", "")
        description = job.get("description", "")
        # Build a short string for this job
        job_parts = []
        if job_title:
            job_parts.append(job_title)
        if company:
            job_parts.append(f"at {company}")
        if industry:
            job_parts.append(f"({industry})")
        if description:
            job_parts.append(f": {description}")
        if job_parts:
            career_texts.append(" ".join(job_parts))
    if career_texts:
        parts.append("Career: " + " | ".join(career_texts))

    # Education – include field of study and institution name (optional)
    edu_texts = []
    for edu in candidate.get("education", []):
        field = edu.get("field_of_study", "")
        institution = edu.get("institution", "")
        if field or institution:
            edu_texts.append(f"{field} at {institution}" if field and institution else field or institution)
    if edu_texts:
        parts.append("Education: " + ", ".join(edu_texts))

    # Combine all parts with newlines
    return "\n".join(parts)

def main():
    print("Loading embedder...")
    embedder = Embedder()

    print("Precomputing JD embedding...")
    jd_text = load_jd_text()
    jd_emb = embedder.embed_single(jd_text)
    np.save(JD_EMBEDDING_PATH, jd_emb)
    print(f"JD embedding saved to {JD_EMBEDDING_PATH}")

    print("Processing candidates...")
    ids = []
    texts = []
    total = 0

    # First pass: build text for all candidates
    for candidate in load_candidates_stream():
        cand_id = candidate["candidate_id"]
        text = build_candidate_text(candidate)
        ids.append(cand_id)
        texts.append(text)
        total += 1
        if total % 10000 == 0:
            print(f"Processed {total} candidates")

    print(f"Total candidates: {total}")
    print(f"Embedding {total} texts in batches...")

    # Embed in batches
    embeddings = embedder.embed(texts, batch_size=BATCH_SIZE, show_progress=True)

    # Save
    np.save(EMBEDDINGS_PATH, embeddings.astype(np.float32))
    with open(IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ids, f)

    print(f"Embeddings saved to {EMBEDDINGS_PATH} (shape: {embeddings.shape})")
    print(f"IDs saved to {IDS_PATH}")
    print("Precompute complete.")

if __name__ == "__main__":
    main()