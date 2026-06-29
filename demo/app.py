import streamlit as st
import json
import gzip
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ranker import compute_final_score
from src.reasoning_generator import generate_reasoning
from src.embedder import get_embedder
from src.jd_parser import load_jd_text

st.set_page_config(page_title="Redrob AI Candidate Ranker", layout="wide")
st.title("🤖 Redrob AI Candidate Ranker")
st.markdown("Rank candidates against the Senior AI Engineer JD")

# ---------- Helper ----------
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
    history = candidate.get("career_history", [])
    for job in history:
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
    return " ".join(parts)

# ---------- Cached Resources ----------
@st.cache_resource
def get_cached_embedder():
    return get_embedder()

@st.cache_resource
def load_jd_embedding():
    embedder = get_cached_embedder()
    jd_text = load_jd_text()
    return embedder.embed_single(jd_text)

# ---------- Sidebar Upload ----------
st.sidebar.header("Upload Candidate Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload candidates file (JSONL, JSONL.gz, or JSON array)",
    type=["jsonl", "gz", "json"]
)

candidates = []
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".gz"):
            with gzip.open(uploaded_file, "rt", encoding="utf-8") as f:
                raw = f.read()
        else:
            raw = uploaded_file.read().decode("utf-8")

        lines = raw.strip().split("\n")
        if len(lines) == 1 and raw.strip().startswith("["):
            # JSON array
            data = json.loads(raw)
            if isinstance(data, list):
                candidates = data
            else:
                st.sidebar.error("Invalid JSON: expected an array")
        else:
            # JSONL
            for line in lines:
                if line.strip():
                    candidates.append(json.loads(line))
        st.sidebar.success(f"Loaded {len(candidates)} candidates")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# ---------- Load sample if available ----------
if not candidates:
    sample_path = Path("data/sample_candidates.json")
    if sample_path.exists():
        with open(sample_path, "r") as f:
            sample_data = json.load(f)
            if isinstance(sample_data, list):
                candidates = sample_data
                st.info("📂 Loaded sample candidates from data/sample_candidates.json")
    else:
        st.info("📤 Please upload a candidates file (JSONL or JSONL.gz) to get started.")

# ---------- Ranking ----------
if candidates:
    if len(candidates) > 1000:
        st.warning(f"⚠️ Large file ({len(candidates)} candidates). Only first 1000 will be ranked for performance.")
        candidates = candidates[:1000]

    if st.button("🚀 Rank Candidates"):
        with st.spinner("Computing embeddings and ranking..."):
            embedder = get_cached_embedder()
            jd_emb = load_jd_embedding()
            norm_jd = jd_emb / np.linalg.norm(jd_emb)

            results = []
            for i, c in enumerate(candidates):
                text = build_candidate_text(c)
                cand_emb = embedder.embed_single(text)
                norm_cand = cand_emb / np.linalg.norm(cand_emb)
                sim = float(np.dot(norm_cand, norm_jd))

                final, scores, is_honeypot, _, _ = compute_final_score(c, sim)
                reasoning = generate_reasoning(c, scores, i+1, is_honeypot)

                results.append({
                    "candidate_id": c.get("candidate_id", f"CAND_{i:07d}"),
                    "name": c.get("profile", {}).get("anonymized_name", "Unknown"),
                    "title": c.get("profile", {}).get("current_title", ""),
                    "yoe": c.get("profile", {}).get("years_of_experience", 0),
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