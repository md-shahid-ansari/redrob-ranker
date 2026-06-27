# Redrob AI Candidate Ranker

> **INDIA RUNS Hackathon — Intelligent Candidate Discovery & Ranking Challenge**

A production-grade AI candidate ranking system that goes beyond keyword matching. It ranks **100,000 candidates** against a job description using semantic similarity, career trajectory analysis, trust-adjusted skill scoring, and behavioral signals.

---

## Architecture

```text
OFFLINE (Run Once)
┌────────────────────────────┐
│ precompute.py              │
│ Generates candidate        │
│ embeddings (~1.5 GB)       │
└──────────────┬─────────────┘
               │
               ▼
      candidate_embeddings.npy

ONLINE (CPU Only, <5 Minutes)
┌────────────────────────────┐
│ rank.py                    │
│ Loads embeddings           │
│ Multi-signal scoring       │
│ Generates submission.csv   │
└────────────────────────────┘
```

---

## Scoring Pipeline

| Signal              | Weight | Description                                              |
| ------------------- | -----: | -------------------------------------------------------- |
| Career Trajectory   |    30% | Product vs. service companies, ML experience, tenure     |
| Skill Fit           |    25% | Trust-adjusted skills using endorsements and duration    |
| Semantic Similarity |    25% | Sentence Transformer embedding similarity                |
| Behavioral Signals  |    15% | Platform activity, response rate, availability           |
| Location            |     5% | Preference for Pune, Noida, Hyderabad, Mumbai, Delhi NCR |

---

## Setup

### Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/redrob-ranker.git
cd redrob-ranker
```

### Create a Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Add Dataset

Place the dataset file in:

```text
data/candidates.jsonl.gz
```

---

## Reproduce the Submission

### 1. Precompute Embeddings (Run Once)

```bash
python precompute.py \
    --candidates data/candidates.jsonl.gz \
    --out data/precomputed/
```

### 2. Rank Candidates

```bash
python rank.py \
    --candidates data/candidates.jsonl.gz \
    --embeddings data/precomputed/ \
    --out submission/submission.csv
```

### 3. Validate Submission

```bash
python validate_submission.py submission/submission.csv
```

---

## Project Structure

```text
redrob-ranker/
├── data/
│   ├── sample_candidates.json
│   ├── job_description.md
│   └── precomputed/
├── src/
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
├── demo/
│   └── app.py
├── notebooks/
│   └── eda.py
├── precompute.py
├── rank.py
├── validate_submission.py
├── submission_metadata.yaml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Tech Stack

* **sentence-transformers** (`all-MiniLM-L6-v2`) – Semantic embeddings
* **FAISS** – Fast vector similarity search
* **NumPy & Pandas** – Data processing
* **Streamlit** – Interactive demo application

---

## Key Design Decisions

### Why No LLM API Calls During Ranking?

The competition requires ranking **100,000 candidates** in under **5 minutes** on **CPU only**, with **no network access**. Calling external LLM APIs would violate these constraints. Instead, embeddings are generated offline and combined with deterministic multi-signal scoring during inference.

### Why Trust-Adjusted Skill Scoring?

A candidate claiming an **Expert** skill with **0 endorsements** and **1 month** of experience should not score the same as someone with **50 endorsements** and **3+ years** of experience. Skill confidence is adjusted using endorsements, duration, and assessment scores.

### Why Penalize Service-Only Careers?

The job description prioritizes candidates with product-company experience. Candidates whose careers are exclusively at companies like TCS, Infosys, Wipro, Cognizant, or Accenture receive a ranking penalty rather than being excluded outright. Previous product-company experience can offset this penalty.

---

## Sandbox

A Streamlit demo will be available here:

```text
https://YOUR_SANDBOX_LINK_HERE
```

---

## Team

**Team:** GSP (Md Shahid Ansari)

**Hackathon:** INDIA RUNS by Redrob AI × Hack2Skill

**Track:** Track 1 — Data & AI Challenge
