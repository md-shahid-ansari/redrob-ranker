import json
import numpy as np
import csv
from pathlib import Path
from tqdm import tqdm
from src.loader import load_candidates_stream
from src.ranker import compute_final_score
from src.reasoning_generator import generate_reasoning
from src.config import TOP_N, TOP_K_FILTER

def main():
    print("Loading precomputed embeddings...")
    embeddings = np.load("data/precomputed/candidate_embeddings.npy")
    with open("data/precomputed/candidate_ids.json", "r") as f:
        candidate_ids = json.load(f)
    jd_embedding = np.load("data/precomputed/jd_embedding.npy")

    id_to_idx = {cid: i for i, cid in enumerate(candidate_ids)}

    print("Computing semantic similarity...")
    norm_emb = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    norm_jd = jd_embedding / np.linalg.norm(jd_embedding)
    similarities = np.dot(norm_emb, norm_jd)

    top_k_indices = np.argsort(similarities)[-TOP_K_FILTER:][::-1]
    top_k_sims = similarities[top_k_indices]
    top_k_ids = [candidate_ids[i] for i in top_k_indices]

    print(f"Filtered to top {TOP_K_FILTER} candidates by semantic similarity.")

    # Load all candidates into a dict (fast)
    print("Loading candidates into memory...")
    candidate_dict = {}
    for c in tqdm(load_candidates_stream(), total=100000, desc="Loading"):
        candidate_dict[c["candidate_id"]] = c

    print("Scoring top K candidates...")
    scored = []
    for cid, sim in tqdm(zip(top_k_ids, top_k_sims), total=len(top_k_ids), desc="Scoring"):
        c = candidate_dict.get(cid)
        if c is None:
            continue
        final, scores, is_honeypot, conf, flags = compute_final_score(c, float(sim))
        scored.append((c, float(sim), final, scores, is_honeypot, conf, flags))

    scored.sort(key=lambda x: x[2], reverse=True)
    top_n = scored[:TOP_N]

    print("Generating reasoning and writing CSV...")
    output_path = Path("submission.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (c, sim, final, scores, is_honeypot, conf, flags) in enumerate(top_n, start=1):
            cid = c["candidate_id"]
            reasoning = generate_reasoning(c, scores, rank, is_honeypot)
            writer.writerow([cid, rank, f"{final:.6f}", reasoning])

    print(f"✅ Submission written to {output_path}")
    print(f"   Top candidate: {top_n[0][0]['candidate_id']} with score {top_n[0][2]:.6f}")
    print(f"   Honeypots in top {TOP_N}: {sum(1 for x in top_n if x[4])}")

if __name__ == "__main__":
    main()