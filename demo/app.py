import streamlit as st
import json
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import load_candidates_stream
from src.ranker import compute_final_score
from src.reasoning_generator import generate_reasoning
from src.embedder import get_embedder
from src.jd_parser import load_jd_text

st.set_page_config(page_title="Redrob AI Candidate Ranker", layout="wide")
st.title("🤖 Redrob AI Candidate Ranker")
st.markdown("Rank candidates against the Senior AI Engineer JD")

# ----- Configuration -----
SAMPLE_SIZE = 100  # candidates to rank in demo without precomputed data

# ----- Helper to build candidate text -----
def build_candidate_text(candidate):
    profile = candidate.get("profile", {})
    parts = [
        profile.get("anonymized_name", ""),
        profile.get("current_title", ""),
        profile.get("summary", ""),
    ]
    skills = candidate.get("skills", [])
    skill_names = [s.get("name", "") for s in skills]
    parts.append(" ".join(skill_names))
    # Also include career history descriptions
    history = candidate.get("career_history", [])
    for job in history:
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
    return " ".join(parts)

# ----- Check for precomputed files -----
PRECOMPUTED_PATH = Path("data/precomputed")
embeddings_exist = (PRECOMPUTED_PATH / "candidate_embeddings.npy").exists()
ids_exist = (PRECOMPUTED_PATH / "candidate_ids.json").exists()
jd_emb_exist = (PRECOMPUTED_PATH / "jd_embedding.npy").exists()

if embeddings_exist and ids_exist and jd_emb_exist:
    @st.cache_resource
    def load_precomputed():
        embeddings = np.load(PRECOMPUTED_PATH / "candidate_embeddings.npy")
        with open(PRECOMPUTED_PATH / "candidate_ids.json", "r") as f:
            ids = json.load(f)
        jd_emb = np.load(PRECOMPUTED_PATH / "jd_embedding.npy")
        return embeddings, ids, jd_emb
    embeddings, candidate_ids, jd_emb = load_precomputed()
    st.success("✅ Precomputed embeddings loaded (full dataset)")
    use_full = True
else:
    st.warning("⚠️ Precomputed embeddings not found. Using on‑the‑fly embeddings for a small sample.")
    use_full = False
    # We'll compute JD embedding once
    embedder = get_embedder()
    jd_text = load_jd_text()
    jd_emb = embedder.embed_single(jd_text)

# ----- Load candidates (full or sample) -----
@st.cache_resource
def load_candidates_map():
    """Return dict of candidate_id -> candidate for all candidates (if using full precomputed)"""
    if use_full:
        return {c["candidate_id"]: c for c in load_candidates_stream()}
    else:
        # Only load SAMPLE_SIZE candidates
        sample = []
        for i, c in enumerate(load_candidates_stream()):
            if i >= SAMPLE_SIZE:
                break
            sample.append(c)
        return {c["candidate_id"]: c for c in sample}

# ----- Main UI -----
option = st.radio("Choose input", ["Sample candidates", "Upload custom JSON"])

if option == "Upload custom JSON":
    uploaded = st.file_uploader("Upload candidates.jsonl (max 100 candidates)", type=["jsonl"])
    if uploaded:
        raw = uploaded.read().decode("utf-8").strip().split("\n")
        target_ids = [json.loads(line)["candidate_id"] for line in raw if line.strip()]
        candidates_map = load_candidates_map()
        target_candidates = [candidates_map[cid] for cid in target_ids if cid in candidates_map]
        st.info(f"Loaded {len(target_candidates)} candidates")
    else:
        target_candidates = []
else:
    candidates_map = load_candidates_map()
    if use_full:
        # Use first 1000 for speed in demo
        target_candidates = list(candidates_map.values())[:1000]
    else:
        target_candidates = list(candidates_map.values())
    st.info(f"Using {len(target_candidates)} candidates")

# ----- Rank button -----
if st.button("🚀 Rank Candidates") and target_candidates:
    with st.spinner("Scoring..."):
        results = []
        if use_full:
            # Precomputed: use dot product with full embeddings
            id_to_idx = {cid: i for i, cid in enumerate(candidate_ids)}
            norm_emb = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            norm_jd = jd_emb / np.linalg.norm(jd_emb)
            for c in target_candidates:
                idx = id_to_idx.get(c["candidate_id"])
                if idx is None:
                    continue
                sim = float(np.dot(norm_emb[idx], norm_jd))
                final, scores, is_honeypot, _, _ = compute_final_score(c, sim)
                reasoning = generate_reasoning(c, scores, len(results)+1, is_honeypot)
                results.append({
                    "candidate_id": c["candidate_id"],
                    "name": c["profile"]["anonymized_name"],
                    "title": c["profile"]["current_title"],
                    "yoe": c["profile"]["years_of_experience"],
                    "score": final,
                    "is_honeypot": is_honeypot,
                    "reasoning": reasoning,
                })
        else:
            # On‑the‑fly: compute embeddings for each candidate
            embedder = get_embedder()
            # Normalize JD embedding once
            norm_jd = jd_emb / np.linalg.norm(jd_emb)
            for c in target_candidates:
                text = build_candidate_text(c)
                cand_emb = embedder.embed_single(text)
                norm_cand = cand_emb / np.linalg.norm(cand_emb)
                sim = float(np.dot(norm_cand, norm_jd))
                final, scores, is_honeypot, _, _ = compute_final_score(c, sim)
                reasoning = generate_reasoning(c, scores, len(results)+1, is_honeypot)
                results.append({
                    "candidate_id": c["candidate_id"],
                    "name": c["profile"]["anonymized_name"],
                    "title": c["profile"]["current_title"],
                    "yoe": c["profile"]["years_of_experience"],
                    "score": final,
                    "is_honeypot": is_honeypot,
                    "reasoning": reasoning,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        df = pd.DataFrame(results)
        st.subheader("📊 Ranked Candidates")
        st.dataframe(df[["candidate_id", "name", "title", "yoe", "score", "is_honeypot"]])

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "demo_submission.csv", "text/csv")