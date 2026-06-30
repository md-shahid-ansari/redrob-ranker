# Redrob AI Candidate Ranker

Rank 100K candidates against a Senior AI Engineer job description.

## 📁 Project Structure

```
redrob-ranker/
├── data/                      # Place input files here
│   ├── candidates.jsonl.gz    # 100K candidate dataset (provided)
│   ├── job_description.docx   # Job description (provided)
│   └── precomputed/           # Generated after precompute (gitignored)
├── src/                       # Scoring modules
│   ├── config.py
│   ├── loader.py
│   ├── jd_parser.py
│   ├── embedder.py
│   ├── career_scorer.py
│   ├── skill_scorer.py
│   ├── behavioral_scorer.py
│   ├── honeypot_detector.py
│   ├── ranker.py
│   └── reasoning_generator.py
├── demo/                      # Streamlit sandbox
│   └── app.py
├── precompute.py              # Generate embeddings (run once)
├── rank.py                    # Main ranking command
├── requirements.txt           # Python dependencies
└── validate_submission.py     # Validation script (provided)
```

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/md-shahid-ansari/redrob-ranker.git
cd redrob-ranker
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# or
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 📥 Data Preparation

Place the following files from the provided bundle into the `data/` folder:

- `candidates.jsonl.gz` – 100K candidate profiles (compressed)
- `job_description.docx` – Senior AI Engineer JD

**Note:** The `data/precomputed/` folder will be generated later; it is ignored by Git to avoid uploading large files.

## ⚙️ Precompute Embeddings (One‑time)

This step creates semantic embeddings for all candidates. It takes ~15–120 minutes depending on your hardware, but only needs to run once.

```bash
python precompute.py
```

After completion, you should see:

- `data/precomputed/candidate_embeddings.npy` (~145 MB)
- `data/precomputed/candidate_ids.json`
- `data/precomputed/jd_embedding.npy`

## 🏆 Rank Candidates

Run the ranking pipeline to produce `submission.csv` with the top 100 candidates.

```bash
python rank.py
```

This loads the precomputed embeddings, scores candidates, and writes the output. Runtime is < 3 minutes on CPU.

## ✅ Validate Submission

Use the provided validation script to check the format and contents of your CSV:

```bash
python validate_submission.py submission.csv
```

Expected output: `Submission is valid.`

## 🧪 Live Sandbox (Streamlit)

You can also run an interactive demo that works on uploaded candidate files (no precompute required for small samples).

```bash
streamlit run demo/app.py
```

A public version is available at:  
[https://redrob-ranker-by-shahid.streamlit.app/](https://redrob-ranker-by-shahid.streamlit.app/)

## 📊 Scoring Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Semantic similarity | 25% | JD‑candidate embedding cosine similarity |
| Career trajectory | 30% | Product vs services companies, ML role fit, YoE, tenure stability |
| Skill matching | 25% | Trust‑adjusted coverage of required skills (endorsements, duration) |
| Behavioral | 15% | Availability, engagement, credibility, market demand |
| Location | 5% | Preference for Pune/Noida/Hyderabad |

Honeypot detection automatically flags and down‑ranks impossible or fraudulent profiles.

## 🧠 Methodology Summary 

- Precompute offline embeddings using `all-MiniLM-L6-v2` (80 MB).
- During ranking, filter to top 5K candidates by semantic similarity.
- Apply five scoring components with configurable weights.
- Generate per‑candidate reasoning referencing actual profile data.
- Final CSV includes candidate ID, rank, score, and reasoning.

## ⚠️ Important Notes

- The `rank.py` script **does not** require network access.
- All models are loaded locally (no external API calls).
- Precomputed embeddings are large; ensure you have enough disk space (~145 MB).
- The sandbox demo runs on‑the‑fly with a small sample, so no precompute is required there.

---

**Team:** Md Shahid Ansari
**Repository:** [https://github.com/md-shahid-ansari/redrob-ranker](https://github.com/md-shahid-ansari/redrob-ranker)