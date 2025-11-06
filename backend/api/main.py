import os
import json
import time
import numpy as np
import pandas as pd
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI

# ------------------ CONFIG ------------------
load_dotenv()
DATA_PATH = "data/clustered_designs.csv"
EMBED_PATH = "data/embeddings_cache.json"
SIM_PATH = "data/similarity_matrix.npy"

# ------------------ INIT ------------------
app = FastAPI(title="VibeBoard API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ LOAD DATA ------------------
print("Loading dataset and embeddings...")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")
if not os.path.exists(EMBED_PATH):
    raise FileNotFoundError(f"Missing embeddings: {EMBED_PATH}")

df = pd.read_csv(DATA_PATH)
with open(EMBED_PATH, "r", encoding="utf-8") as f:
    embeddings = json.load(f)

urls = list(embeddings.keys())
emb_matrix = np.array(list(embeddings.values()))

# Load precomputed similarity if exists
if os.path.exists(SIM_PATH):
    try:
        similarity_matrix = np.load(SIM_PATH)
    except Exception:
        similarity_matrix = None
else:
    similarity_matrix = None

# ------------------ OPENAI CLIENT ------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@lru_cache(maxsize=1024)
def encode_query_cached(query: str) -> np.ndarray:
    """Encode query using OpenAI embedding (same model used for dataset)."""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# ------------------ HELPERS ------------------
def confidence(sim):
    return float((sim + 1.0) / 2.0)

# ------------------ ROUTES ------------------

@app.get("/")
def root():
    return {"message": "Welcome to VibeBoard API"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "rows": len(df),
        "embeddings": len(emb_matrix),
        "similarity_matrix": similarity_matrix is not None,
        "embedding_model": "text-embedding-3-large (OpenAI)"
    }

@app.get("/search")
def search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=100)):
    try:
        q = q.strip()
        query_emb = encode_query_cached(q)
        sims = cosine_similarity(emb_matrix, query_emb.reshape(1, -1)).flatten()
        top_idx = np.argsort(-sims)[:top_k]

        results = []
        for i in top_idx:
            url = urls[i]
            row = df[df["url"] == url]
            if row.empty:
                continue
            item = row.iloc[0].to_dict()
            item["_score"] = float(sims[i])
            item["confidence"] = confidence(sims[i])
            results.append(item)

        return {"query": q, "results": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/related")
def related(url: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
    if url not in embeddings:
        return {"error": "URL not found in embeddings"}

    idx = urls.index(url)
    if similarity_matrix is not None and similarity_matrix.shape[0] == len(urls):
        sims = similarity_matrix[idx]
    else:
        sims = cosine_similarity([emb_matrix[idx]], emb_matrix).flatten()

    top_idx = np.argsort(-sims)[1: top_k + 1]
    results = []
    for i in top_idx:
        rurl = urls[i]
        row = df[df["url"] == rurl]
        if row.empty:
            continue
        item = row.iloc[0].to_dict()
        item["_score"] = float(sims[i])
        item["confidence"] = confidence(sims[i])
        results.append(item)

    return {"url": url, "related": results}

@app.get("/designs")
def get_designs(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "page": page,
        "total": len(df),
        "data": df.iloc[start:end].to_dict(orient="records")
    }

@app.get("/clusters")
def clusters(sample_per_cluster: int = Query(5, ge=1, le=50)):
    if "cluster" not in df.columns:
        return {"error": "No cluster column in dataset"}
    result = []
    for c, g in df.groupby("cluster"):
        sample = g.sample(min(sample_per_cluster, len(g))).to_dict(orient="records")
        result.append({"cluster": int(c), "count": len(g), "examples": sample})
    return {"clusters": result}
