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

st.set_page_config(page_title="Redrob AI Candidate Ranker", layout="wide")
st.title("🤖 Redrob AI Candidate Ranker")
st.markdown("Rank candidates against the Senior AI Engineer JD")

# Load precomputed data
@st.cache_resource
def load_embeddings():
    embeddings = np.load("data/precomputed/candidate_embeddings.npy")
    with open("data/precomputed/candidate_ids.json", "r") as f:
        ids = json.load(f)
    jd_emb = np.load("data/precomputed/jd_embedding.npy")
    return embeddings, ids, jd_emb

try:
    embeddings, candidate_ids, jd_emb = load_embeddings()
    st.success("✅ Precomputed embeddings loaded")
except FileNotFoundError:
    st.error("Please run `python precompute.py` first.")
    st.stop()

# Load candidates into memory (cached)
@st.cache_resource
def load_candidates():
    return {c["candidate_id"]: c for c in load_candidates_stream()}

candidates_dict = load_candidates()

# Sidebar: input method
option = st.radio("Choose input", ["Sample candidates (first 1000)", "Upload custom JSON"])

if option == "Upload custom JSON":
    uploaded = st.file_uploader("Upload candidates.jsonl (max 100 candidates)", type=["jsonl"])
    if uploaded:
        raw = uploaded.read().decode("utf-8").strip().split("\n")
        target_ids = [json.loads(line)["candidate_id"] for line in raw if line.strip()]
        target_candidates = [candidates_dict[cid] for cid in target_ids if cid in candidates_dict]
        st.info(f"Loaded {len(target_candidates)} candidates")
    else:
        target_candidates = []
else:
    # Use first 1000 candidates from dataset (quick demo)
    st.info("Using first 1000 candidates (subset of full dataset)")
    target_candidates = []
    for i, c in enumerate(load_candidates_stream()):
        if i >= 1000:
            break
        target_candidates.append(c)

# Ranking
if st.button("🚀 Rank Candidates") and target_candidates:
    with st.spinner("Scoring..."):
        # Compute similarities for selected candidates
        id_to_idx = {cid: i for i, cid in enumerate(candidate_ids)}
        norm_emb = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        norm_jd = jd_emb / np.linalg.norm(jd_emb)

        results = []
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

        results.sort(key=lambda x: x["score"], reverse=True)
        df = pd.DataFrame(results)

        st.subheader("📊 Ranked Candidates")
        st.dataframe(df[["rank", "candidate_id", "name", "title", "yoe", "score", "is_honeypot"]])

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "demo_submission.csv", "text/csv")