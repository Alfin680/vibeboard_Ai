# backend/api/main.py
import os
import json
import logging
from functools import lru_cache
from typing import List

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity

# Optional groq client; import only if available
try:
    from groq import Groq
except Exception:
    Groq = None  # we'll handle gracefully

# Optional supabase client
try:
    from supabase import create_client  # supabase-py v1
except Exception:
    create_client = None

load_dotenv()

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vibeboard-api")

# ------------------ CONFIG (ENV) ------------------
DATA_PATH = os.environ.get("DATA_PATH", "data/clustered_designs.csv")
EMBED_PATH = os.environ.get("EMBED_PATH", "data/embeddings_cache.json")
SIM_PATH = os.environ.get("SIM_PATH", "data/similarity_matrix.npy")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ------------------ APP INIT ------------------
app = FastAPI(title="VibeBoard API (clean)", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ SUPABASE CLIENT ------------------
supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized.")
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        supabase = None
else:
    logger.warning("Supabase client not configured (missing package or env).")

# ------------------ GROQ CLIENT (optional) ------------------
groq_client = None
if Groq and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized.")
    except Exception as e:
        logger.warning("Failed to initialize Groq client: %s", e)
else:
    if not Groq:
        logger.info("Groq library is not installed; generate endpoint will fallback.")
    else:
        logger.info("GROQ_API_KEY not set; generate endpoint will fallback.")

# ------------------ OPENAI CLIENT ------------------
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized.")
    except Exception as e:
        logger.warning("Failed to initialize OpenAI client: %s", e)
else:
    logger.warning("OPENAI_API_KEY not set. Embeddings endpoint will fail if called.")

# ------------------ LOAD DATA & EMBEDDINGS ------------------
if not os.path.exists(DATA_PATH):
    logger.error("Missing dataset file: %s", DATA_PATH)
    raise FileNotFoundError(f"Missing dataset file: {DATA_PATH}")

if not os.path.exists(EMBED_PATH):
    logger.error("Missing embeddings file: %s", EMBED_PATH)
    raise FileNotFoundError(f"Missing embeddings file: {EMBED_PATH}")

logger.info("Loading dataset and embeddings...")
df = pd.read_csv(DATA_PATH)

with open(EMBED_PATH, "r", encoding="utf-8") as f:
    embeddings = json.load(f)

urls = list(embeddings.keys())
emb_matrix = np.array(list(embeddings.values()), dtype=np.float32)

similarity_matrix = None
if os.path.exists(SIM_PATH):
    try:
        similarity_matrix = np.load(SIM_PATH)
        logger.info("Loaded precomputed similarity matrix.")
    except Exception:
        similarity_matrix = None

# ------------------ HELPERS ------------------
@lru_cache(maxsize=1024)
def encode_query_cached(query: str):
    if not openai_client:
        raise RuntimeError("OpenAI client not configured")
    resp = openai_client.embeddings.create(model="text-embedding-3-large", input=query)
    return np.array(resp.data[0].embedding, dtype=np.float32)

def confidence(sim: float) -> float:
    return float((sim + 1.0) / 2.0)

# ------------------ Pydantic Models ------------------
class HistoryItem(BaseModel):
    user_id: str
    query: str

# ------------------ ROUTES (search / related / designs) ------------------
@app.get("/")
def root():
    return {"message": "VibeBoard API running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "rows": len(df),
        "embeddings_count": len(emb_matrix),
        "similarity_precomputed": similarity_matrix is not None,
    }

@app.get("/search")
def search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=100)):
    try:
        q = q.strip()
        q_emb = encode_query_cached(q)
        sims = cosine_similarity(emb_matrix, q_emb.reshape(1, -1)).flatten()
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
        logger.exception("Error in /search: %s", e)
        return {"error": str(e)}

@app.get("/related")
def related(url: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
    try:
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
    except Exception as e:
        logger.exception("Error in /related: %s", e)
        return {"error": str(e)}

@app.get("/designs")
def designs(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    start = (page - 1) * per_page
    end = start + per_page
    return {"page": page, "total": len(df), "data": df.iloc[start:end].to_dict(orient="records")}

# ------------------ HISTORY (supabase) ------------------
@app.post("/history/add")
def add_history(item: HistoryItem):
    if not supabase:
        return {"error": "Supabase not configured"}
    try:
        resp = supabase.table("search_history").insert({
            "user_id": item.user_id,
            "query": item.query
        }).execute()
        logger.debug("history insert response: %s", resp)
        return {"status": "success"}
    except Exception as e:
        logger.exception("Failed to insert history: %s", e)
        return {"error": str(e)}

@app.get("/history/{user_id}")
def get_history(user_id: str):
    if not supabase:
        return {"error": "Supabase not configured"}
    try:
        resp = supabase.table("search_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return resp.data
    except Exception as e:
        logger.exception("Failed to fetch history: %s", e)
        return {"error": str(e)}

# ------------------ LIKES (keep endpoints under /api/likes/*) ------------------
@app.post("/api/likes/add")
def add_like(user_id: str = Body(...), url: str = Body(...), title: str = Body(""), image: str = Body(""), caption: str = Body("")):
    if not supabase:
        return {"error": "Supabase not configured"}
    try:
        resp = supabase.table("likes").insert({
            "user_id": user_id,
            "url": url,
            "title": title,
            "image": image,
            "caption": caption,
        }).execute()
        logger.info("Supabase likes.insert response: %s", getattr(resp, "__dict__", resp))
        if getattr(resp, "error", None):
            return {"error": str(resp.error)}
        return {"status": "liked"}
    except Exception as e:
        logger.exception("Failed to insert like: %s", e)
        return {"error": str(e)}

@app.post("/api/likes/remove")
def remove_like(user_id: str = Body(...), url: str = Body(...)):
    if not supabase:
        return {"error": "Supabase not configured"}
    try:
        resp = supabase.table("likes").delete().match({"user_id": user_id, "url": url}).execute()
        logger.info("Supabase likes.delete response: %s", getattr(resp, "__dict__", resp))
        return {"status": "unliked"}
    except Exception as e:
        logger.exception("Failed to delete like: %s", e)
        return {"error": str(e)}

@app.post("/api/likes/status")
def like_status(user_id: str = Body(...), urls: List[str] = Body(...)):
    if not supabase:
        return {"error": "Supabase not configured"}
    try:
        resp = supabase.table("likes").select("url").eq("user_id", user_id).in_("url", urls).execute()
        data = resp.data or []
        liked_urls = {row["url"]: True for row in data}
        return liked_urls
    except Exception as e:
        logger.exception("Failed in like_status: %s", e)
        return {"error": str(e)}

# ------------------ designs batch (for saved page) ------------------
@app.post("/api/designs/batch")
def batch_designs(urls: List[str] = Body(...)):
    try:
        results = []
        for u in urls:
            row = df[df["url"] == u]
            if not row.empty:
                results.append(row.iloc[0].to_dict())
        return {"designs": results}
    except Exception as e:
        logger.exception("Failed in /api/designs/batch: %s", e)
        return {"error": str(e)}

# ------------------ GENERATE (Groq or fallback) ------------------
@app.get("/api/generate-idea")
def generate_idea():
    fallback_prompts = [
        "Minimalist fintech dashboard with soft gradients",
        "Luxury eCommerce landing page with serif typography",
        "Vibrant portfolio site with animated transitions",
        "Dark-mode SaaS interface with neon accents",
        "Calm wellness app UI with pastel colors"
    ]

    prompt = (
        "Generate a single creative website UI concept description. "
        "It must be short (max 10 words), focused on style, color, and mood. "
        "Return ONLY the description. "
        "Examples: " + ", ".join(fallback_prompts)
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=30,
        )

        idea = completion.choices[0].message.content.strip()

        # Safety fallback if model goes rogue
        if not idea or len(idea.split()) < 6:
            return {"idea": np.random.choice(fallback_prompts)}

        return {"idea": idea}

    except Exception as e:
        logger.exception("Groq generation failed: %s", e)
        return {"idea": np.random.choice(fallback_prompts)}
