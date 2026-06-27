# Scoring weights (will be used in ranker)
WEIGHTS = {
    "semantic": 0.25,
    "career": 0.30,
    "skill": 0.25,
    "behavioral": 0.15,
    "location": 0.05,
}

# Honeypot thresholds
HONEYPOT = {
    "salary_inversion": True,          # min > max
    "signup_after_last_active": True,
    "age_impossible": True,            # e.g., career_start < 16
    "skill_fraud": {
        "min_expert_skills": 5,        # if >=5 expert skills with 0 endorsements & <6 months
        "endorsement_farming": 50,     # endorsements > 50 for beginner skill with short duration
    }
}

# Industry scoring
INDUSTRY_SCORES = {
    "AI/ML": 1.0,
    "Software": 0.8,
    "Fintech": 0.9,
    "Food Delivery": 0.8,
    "E-commerce": 0.7,
    "AdTech": 0.8,
    "SaaS": 0.8,
    "EdTech": 0.7,
    "Transportation": 0.6,
    "Consulting": 0.5,
    "IT Services": 0.1,
    "Manufacturing": 0.2,
    "Conglomerate": 0.2,
    "Paper Products": 0.1,
    "Insurance Tech": 0.6,
    # default: 0.3
}

# Services companies (blacklist for penalisation)
SERVICES_COMPANIES = {
    "infosys", "wipro", "tcs", "accenture", "capgemini", "hcl",
    "cognizant", "mindtree", "tech mahindra", "lti", "mphasis", "hexaware",
    "virtusa", "ust global", "ibm services", "delloitte", "pwc", "ey",
}

# Product companies (positive boost)
PRODUCT_COMPANIES = {
    "swiggy", "zomato", "ola", "razorpay", "cred", "paytm", "flipkart",
    "amazon", "google", "microsoft", "uber", "airbnb", "netflix", "spotify",
    "pied piper", "hooli", "initech", "globex inc", "acme corp", "wayne enterprises",
    "stark industries", "dunder mifflin", # These are fictional but we treat them as product
}

# ML/AI title keywords for title scoring
ML_TITLE_KEYWORDS = [
    "ai", "machine learning", "ml", "nlp", "data scientist", "search",
    "recommendation", "ranking", "retrieval", "applied", "deep learning",
    "reinforcement learning", "computer vision", "speech", "llm", "generative ai",
    "prompt engineer", "rag", "vector", "embedding", "pytorch", "tensorflow"
]

# Required skills from JD (we'll parse JD to enrich this)
JD_REQUIRED_SKILLS = {
    "embeddings", "vector search", "faiss", "pinecone", "weaviate", "qdrant",
    "milvus", "elasticsearch", "opensearch", "sentence-transformers",
    "hugging face transformers", "fine-tuning llms", "lora", "peft",
    "langchain", "haystack", "rag", "prompt engineering",
    "python", "mlops", "kubeflow", "mlflow",
    "evaluation", "benchmarking", "retrieval", "hybrid search", "reranking",
    "information retrieval", "bm25", "feature engineering",
}
# Nice-to-have
JD_NICE_TO_HAVE = {
    "airflow", "docker", "kubernetes", "ci/cd", "terraform",
    "spark", "hadoop", "bigquery", "databricks", "gcp", "aws", "azure",
}

# Location preference (JD says Pune, Noida, Hyderabad, Mumbai, Delhi NCR)
PREFERRED_LOCATIONS = {"pune", "noida", "hyderabad", "mumbai", "delhi ncr", "gurugram"}

# YoE ideal range
YOE_IDEAL_MIN = 5
YOE_IDEAL_MAX = 9

# Notice period preference (days)
NOTICE_PREFERRED = 30

# Last active preference (days)
LAST_ACTIVE_PREFERRED = 30

# Behavioural thresholds
RESPONSE_RATE_GOOD = 0.5
INTERVIEW_COMPLETION_GOOD = 0.8
OFFER_ACCEPTANCE_GOOD = 0.5  # moderate

# Skill trust weights
TRUST_WEIGHTS = {
    "endorsement": 0.4,
    "duration_months": 0.3,
    "assessment_score": 0.3,
}