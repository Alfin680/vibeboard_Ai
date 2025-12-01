import os
import json
import numpy as np
import pandas as pd
from typing import Optional, List
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from backend.db.supabase_client import supabase
from backend.ai.groq_client import groq_client

from backend.api.search import router as search_router
from backend.api.generate import router as generate_router

# ------------------ CONFIG ------------------
load_dotenv()
DATA_PATH = "data/clustered_designs.csv"
EMBED_PATH = "data/embeddings_cache.json"
SIM_PATH = "data/similarity_matrix.npy"

# ------------------ INIT APP ------------------
app = FastAPI(title="VibeBoard API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: Option B → NO PREFIX
app.include_router(generate_router)
app.include_router(search_router)

# ------------------ LOAD DATA ------------------
print("Loading dataset and embeddings...")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing dataset file: {DATA_PATH}")

if not os.path.exists(EMBED_PATH):
    raise FileNotFoundError(f"Missing embeddings file: {EMBED_PATH}")

df = pd.read_csv(DATA_PATH)

with open(EMBED_PATH, "r", encoding="utf-8") as f:
    embeddings = json.load(f)

urls = list(embeddings.keys())
emb_matrix = np.array(list(embeddings.values()))

similarity_matrix = None
if os.path.exists(SIM_PATH):
    try:
        similarity_matrix = np.load(SIM_PATH)
    except:
        similarity_matrix = None

# ------------------ OPENAI CLIENT ------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@lru_cache(maxsize=1024)
def encode_query_cached(query: str) -> np.ndarray:
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
    return {"message": "VibeBoard API running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "rows": len(df),
        "embeddings_count": len(emb_matrix),
        "similarity_precomputed": similarity_matrix is not None,
        "embedding_model": "text-embedding-3-large"
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

    top_idx = np.argsort(-sims)[1 : top_k + 1]

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
    return {"page": page, "total": len(df), "data": df.iloc[start:end].to_dict(orient="records")}

# ------------------ HISTORY ------------------

class HistoryItem(BaseModel):
    user_id: str
    query: str

@app.post("/history/add")
def add_history(item: HistoryItem):
    try:
        supabase.table("search_history").insert({
            "user_id": item.user_id,
            "query": item.query
        }).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/history/{user_id}")
def get_history(user_id: str):
    try:
        response = (
            supabase.table("search_history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        return {"error": str(e)}

# ------------------ LIKES (OPTION B ROUTES) ------------------

@app.post("/likes/add")
def add_like(
    user_id: str = Body(...),
    url: str = Body(...),
    title: str = Body(""),
    image: str = Body(""),
    caption: str = Body("")
):
    try:
        supabase.table("likes").insert({
            "user_id": user_id,
            "url": url,
            "title": title,
            "image": image,
            "caption": caption,
        }).execute()

        return {"status": "liked"}

    except Exception as e:
        return {"error": str(e)}

@app.post("/likes/remove")
def remove_like(
    user_id: str = Body(...),
    url: str = Body(...)
):
    try:
        supabase.table("likes").delete().match({
            "user_id": user_id,
            "url": url
        }).execute()

        return {"status": "unliked"}

    except Exception as e:
        return {"error": str(e)}

@app.post("/likes/status")
def like_status(
    user_id: str = Body(...),
    urls: list[str] = Body(...)
):
    try:
        response = (
            supabase.table("likes")
            .select("url")
            .eq("user_id", user_id)
            .in_("url", urls)
            .execute()
        )

        liked_urls = {row["url"]: True for row in response.data}
        return liked_urls

    except Exception as e:
        return {"error": str(e)}
# import os
# import json
# import time
# import numpy as np
# import pandas as pd
# from typing import Optional
# from fastapi import FastAPI, Query
# from fastapi.middleware.cors import CORSMiddleware
# from sklearn.metrics.pairwise import cosine_similarity
# from functools import lru_cache
# from dotenv import load_dotenv
# from openai import OpenAI
# from db.supabase_client import supabase
# from fastapi import Body

# # ------------------ CONFIG ------------------
# load_dotenv()
# DATA_PATH = "data/clustered_designs.csv"
# EMBED_PATH = "data/embeddings_cache.json"
# SIM_PATH = "data/similarity_matrix.npy"

# # ------------------ INIT ------------------
# app = FastAPI(title="VibeBoard API", version="1.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ------------------ LOAD DATA ------------------
# print("Loading dataset and embeddings...")

# if not os.path.exists(DATA_PATH):
#     raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")
# if not os.path.exists(EMBED_PATH):
#     raise FileNotFoundError(f"Missing embeddings: {EMBED_PATH}")

# df = pd.read_csv(DATA_PATH)
# with open(EMBED_PATH, "r", encoding="utf-8") as f:
#     embeddings = json.load(f)

# urls = list(embeddings.keys())
# emb_matrix = np.array(list(embeddings.values()))

# # Load precomputed similarity if exists
# if os.path.exists(SIM_PATH):
#     try:
#         similarity_matrix = np.load(SIM_PATH)
#     except Exception:
#         similarity_matrix = None
# else:
#     similarity_matrix = None

# # ------------------ OPENAI CLIENT ------------------
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# @lru_cache(maxsize=1024)
# def encode_query_cached(query: str) -> np.ndarray:
#     """Encode query using OpenAI embedding (same model used for dataset)."""
#     response = client.embeddings.create(
#         model="text-embedding-3-large",
#         input=query
#     )
#     return np.array(response.data[0].embedding, dtype=np.float32)

# # ------------------ HELPERS ------------------
# def confidence(sim):
#     return float((sim + 1.0) / 2.0)

# # ------------------ ROUTES ------------------

# @app.get("/")
# def root():
#     return {"message": "Welcome to VibeBoard API"}

# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "rows": len(df),
#         "embeddings": len(emb_matrix),
#         "similarity_matrix": similarity_matrix is not None,
#         "embedding_model": "text-embedding-3-large (OpenAI)"
#     }

# @app.get("/search")
# def search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=100)):
#     try:
#         q = q.strip()
#         query_emb = encode_query_cached(q)
#         sims = cosine_similarity(emb_matrix, query_emb.reshape(1, -1)).flatten()
#         top_idx = np.argsort(-sims)[:top_k]

#         results = []
#         for i in top_idx:
#             url = urls[i]
#             row = df[df["url"] == url]
#             if row.empty:
#                 continue
#             item = row.iloc[0].to_dict()
#             item["_score"] = float(sims[i])
#             item["confidence"] = confidence(sims[i])
#             results.append(item)

#         return {"query": q, "results": results}
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return {"error": str(e)}

# @app.get("/related")
# def related(url: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
#     if url not in embeddings:
#         return {"error": "URL not found in embeddings"}

#     idx = urls.index(url)
#     if similarity_matrix is not None and similarity_matrix.shape[0] == len(urls):
#         sims = similarity_matrix[idx]
#     else:
#         sims = cosine_similarity([emb_matrix[idx]], emb_matrix).flatten()

#     top_idx = np.argsort(-sims)[1: top_k + 1]
#     results = []
#     for i in top_idx:
#         rurl = urls[i]
#         row = df[df["url"] == rurl]
#         if row.empty:
#             continue
#         item = row.iloc[0].to_dict()
#         item["_score"] = float(sims[i])
#         item["confidence"] = confidence(sims[i])
#         results.append(item)

#     return {"url": url, "related": results}

# @app.get("/designs")
# def get_designs(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
#     start = (page - 1) * per_page
#     end = start + per_page
#     return {
#         "page": page,
#         "total": len(df),
#         "data": df.iloc[start:end].to_dict(orient="records")
#     }

# @app.get("/clusters")
# def clusters(sample_per_cluster: int = Query(5, ge=1, le=50)):
#     if "cluster" not in df.columns:
#         return {"error": "No cluster column in dataset"}
#     result = []
#     for c, g in df.groupby("cluster"):
#         sample = g.sample(min(sample_per_cluster, len(g))).to_dict(orient="records")
#         result.append({"cluster": int(c), "count": len(g), "examples": sample})
#     return {"clusters": result}


# @app.post("/history/add")
# def add_history(user_id: str = Body(...), query: str = Body(...)):
#     try:
#         supabase.table("search_history").insert({"user_id": user_id, "query": query}).execute()
#         return {"status": "success"}
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/history/{user_id}")
# def get_history(user_id: str):
#     try:
#         response = supabase.table("search_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
#         return response.data
#     except Exception as e:
#         return {"error": str(e)}


#========================================================
# import os
# import json
# import numpy as np
# import pandas as pd
# from typing import Optional, List
# from fastapi import FastAPI, Query, Body
# from fastapi.middleware.cors import CORSMiddleware
# from sklearn.metrics.pairwise import cosine_similarity
# from functools import lru_cache
# from dotenv import load_dotenv
# from openai import OpenAI
# from pydantic import BaseModel

# from backend.db.supabase_client import supabase
# from backend.ai.groq_client import groq_client

# from fastapi import FastAPI
# from backend.api.search import router as search_router
# from backend.api.generate import router as generate_router







# # ------------------ CONFIG ------------------
# load_dotenv()
# DATA_PATH = "data/clustered_designs.csv"
# EMBED_PATH = "data/embeddings_cache.json"
# SIM_PATH = "data/similarity_matrix.npy"


# # ------------------ INIT APP ------------------
# app = FastAPI(title="VibeBoard API", version="1.0")


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Replace with domain in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.include_router(generate_router, prefix="/api")
# app.include_router(search_router, prefix="/api") 
# # ------------------ LOAD DATA ------------------
# print("Loading dataset and embeddings...")

# if not os.path.exists(DATA_PATH):
#     raise FileNotFoundError(f"Missing dataset file: {DATA_PATH}")

# if not os.path.exists(EMBED_PATH):
#     raise FileNotFoundError(f"Missing embeddings file: {EMBED_PATH}")

# df = pd.read_csv(DATA_PATH)

# with open(EMBED_PATH, "r", encoding="utf-8") as f:
#     embeddings = json.load(f)

# urls = list(embeddings.keys())
# emb_matrix = np.array(list(embeddings.values()))

# similarity_matrix = None
# if os.path.exists(SIM_PATH):
#     try:
#         similarity_matrix = np.load(SIM_PATH)
#     except:
#         similarity_matrix = None


# # ------------------ OPENAI CLIENT ------------------
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# @lru_cache(maxsize=1024)
# def encode_query_cached(query: str) -> np.ndarray:
#     """Encode text using the same embeddings model used for dataset."""
#     response = client.embeddings.create(
#         model="text-embedding-3-large",
#         input=query
#     )
#     return np.array(response.data[0].embedding, dtype=np.float32)

# # @app.get("/api/generate-idea")
# # def generate_ui_idea():
# #     prompt = """
# #     Generate one creative website/app UI idea.
# #     Keep it short, visual, and concrete.
# #     Output only the idea, no extra text.
# #     """

# #     completion = groq_client.chat.completions.create(
# #         model="llama3-8b-8192",
# #         messages=[{"role": "user", "content": prompt}],
# #         temperature=0.7
# #     )

# #     idea = completion.choices[0].message["content"].strip()
# #     return {"idea": idea}
# # ------------------ HELPERS ------------------
# def confidence(sim):
#     return float((sim + 1.0) / 2.0)


# # ------------------ ROUTES ------------------
# @app.get("/")
# def root():
#     return {"message": "VibeBoard API running"}


# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "rows": len(df),
#         "embeddings_count": len(emb_matrix),
#         "similarity_precomputed": similarity_matrix is not None,
#         "embedding_model": "text-embedding-3-large"
#     }


# @app.get("/search")
# def search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=100)):
#     try:
#         q = q.strip()
#         query_emb = encode_query_cached(q)
#         sims = cosine_similarity(emb_matrix, query_emb.reshape(1, -1)).flatten()
#         top_idx = np.argsort(-sims)[:top_k]

#         results = []
#         for i in top_idx:
#             url = urls[i]
#             row = df[df["url"] == url]
#             if row.empty:
#                 continue
#             item = row.iloc[0].to_dict()
#             item["_score"] = float(sims[i])
#             item["confidence"] = confidence(sims[i])
#             results.append(item)

#         return {"query": q, "results": results}

#     except Exception as e:
#         return {"error": str(e)}


# @app.get("/related")
# def related(url: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
#     if url not in embeddings:
#         return {"error": "URL not found in embeddings"}

#     idx = urls.index(url)

#     if similarity_matrix is not None and similarity_matrix.shape[0] == len(urls):
#         sims = similarity_matrix[idx]
#     else:
#         sims = cosine_similarity([emb_matrix[idx]], emb_matrix).flatten()

#     top_idx = np.argsort(-sims)[1 : top_k + 1]

#     results = []
#     for i in top_idx:
#         rurl = urls[i]
#         row = df[df["url"] == rurl]
#         if row.empty:
#             continue
#         item = row.iloc[0].to_dict()
#         item["_score"] = float(sims[i])
#         item["confidence"] = confidence(sims[i])
#         results.append(item)

#     return {"url": url, "related": results}


# @app.get("/designs")
# def get_designs(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
#     start = (page - 1) * per_page
#     end = start + per_page
#     return {"page": page, "total": len(df), "data": df.iloc[start:end].to_dict(orient="records")}


# # ------------------ SUPABASE HISTORY ------------------

# class HistoryItem(BaseModel):
#     user_id: str
#     query: str

# @app.post("/history/add")
# def add_history(item: HistoryItem):
#     try:
#         supabase.table("search_history").insert({
#             "user_id": item.user_id,
#             "query": item.query
#         }).execute()
#         return {"status": "success"}
#     except Exception as e:
#         return {"error": str(e)}


# @app.get("/history/{user_id}")
# def get_history(user_id: str):
#     try:
#         response = (
#             supabase.table("search_history")
#             .select("*")
#             .eq("user_id", user_id)
#             .order("created_at", desc=True)
#             .execute()
#         )
#         return response.data
#     except Exception as e:
#         return {"error": str(e)}

# @app.post("/api/likes/add")
# def add_like(
#     user_id: str = Body(...),
#     url: str = Body(...),
#     title: str = Body(""),
#     image: str = Body(""),
#     caption: str = Body("")
# ):
#     try:
#         supabase.table("likes").insert({
#             "user_id": user_id,
#             "url": url,
#             "title": title,
#             "image": image,
#             "caption": caption,
#         }).execute()

#         return {"status": "liked"}

#     except Exception as e:
#         return {"error": str(e)}

# @app.post("/api/likes/remove")
# def remove_like(
#     user_id: str = Body(...),
#     url: str = Body(...)
# ):
#     try:
#         supabase.table("likes").delete().match({
#             "user_id": user_id,
#             "url": url
#         }).execute()

#         return {"status": "unliked"}

#     except Exception as e:
#         return {"error": str(e)}
        
# @app.post("/api/likes/status")
# def like_status(
#     user_id: str = Body(...),
#     urls: list[str] = Body(...)
# ):
#     try:
#         response = supabase.table("likes") \
#             .select("url") \
#             .eq("user_id", user_id) \
#             .in_("url", urls) \
#             .execute()

#         liked_urls = {row["url"]: True for row in response.data}
#         return liked_urls

#     except Exception as e:
#         return {"error": str(e)}
#===========================================================

import os
import json
import numpy as np
import pandas as pd
from typing import Optional, List
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from backend.db.supabase_client import supabase
from backend.ai.groq_client import groq_client

from backend.api.search import router as search_router
from backend.api.generate import router as generate_router


# ------------------ CONFIG ------------------
load_dotenv()
DATA_PATH = "data/clustered_designs.csv"
EMBED_PATH = "data/embeddings_cache.json"
SIM_PATH = "data/similarity_matrix.npy"


# ------------------ INIT APP ------------------
app = FastAPI(title="VibeBoard API", version="1.0")

#app.include_router(likes_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # Replace with domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api")
app.include_router(search_router, prefix="/api")


# ------------------ LOAD DATA ------------------
print("Loading dataset and embeddings...")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing dataset file: {DATA_PATH}")

if not os.path.exists(EMBED_PATH):
    raise FileNotFoundError(f"Missing embeddings file: {EMBED_PATH}")

df = pd.read_csv(DATA_PATH)

with open(EMBED_PATH, "r", encoding="utf-8") as f:
    embeddings = json.load(f)

urls = list(embeddings.keys())
emb_matrix = np.array(list(embeddings.values()))

similarity_matrix = None
if os.path.exists(SIM_PATH):
    try:
        similarity_matrix = np.load(SIM_PATH)
    except:
        similarity_matrix = None


# ------------------ OPENAI CLIENT ------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@lru_cache(maxsize=1024)
def encode_query_cached(query: str) -> np.ndarray:
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
    return {"message": "VibeBoard API running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rows": len(df),
        "embeddings_count": len(emb_matrix),
        "similarity_precomputed": similarity_matrix is not None,
        "embedding_model": "text-embedding-3-large",
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
    return {"page": page, "total": len(df), "data": df.iloc[start:end].to_dict(orient="records")}


# ------------------ SUPABASE HISTORY ------------------
class HistoryItem(BaseModel):
    user_id: str
    query: str


@app.post("/history/add")
def add_history(item: HistoryItem):
    try:
        supabase.table("search_history").insert({
            "user_id": item.user_id,
            "query": item.query,
        }).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/history/{user_id}")
def get_history(user_id: str):
    try:
        response = (
            supabase.table("search_history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        return {"error": str(e)}


# ------------------ LIKES (LIKE / UNLIKE / STATUS) ------------------
@app.post("/api/likes/add")
def add_like(
    user_id: str = Body(...),
    url: str = Body(...),
    title: str = Body(""),
    image: str = Body(""),
    caption: str = Body("")
):
    try:
        response = supabase.table("likes").insert({
            "user_id": user_id,
            "url": url,
            "title": title,
            "image": image,
            "caption": caption,
        }).execute()

        print("SUPABASE INSERT RESPONSE:", response)

        if response.error:
            print("SUPABASE INSERT ERROR:", response.error)
            return {"error": str(response.error)}

        return {"status": "liked"}

    except Exception as e:
        print("EXCEPTION DURING LIKE INSERT:", str(e))
        return {"error": str(e)}



@app.post("/api/likes/remove")
def remove_like(
    user_id: str = Body(...),
    url: str = Body(...),
):
    try:
        supabase.table("likes").delete().match({
            "user_id": user_id,
            "url": url,
        }).execute()

        return {"status": "unliked"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/likes/status")
def like_status(
    user_id: str = Body(...),
    urls: list[str] = Body(...),
):
    try:
        response = (
            supabase.table("likes")
            .select("url")
            .eq("user_id", user_id)
            .in_("url", urls)
            .execute()
        )

        liked_urls = {row["url"]: True for row in response.data}
        return liked_urls

    except Exception as e:
        return {"error": str(e)}


# ------------------ NEW: FETCH FULL DESIGN INFO FROM URL LIST ------------------
@app.post("/api/designs/batch")
def batch_designs(urls: list[str] = Body(...)):
    try:
        results = []
        for url in urls:
            row = df[df["url"] == url]
            if not row.empty:
                results.append(row.iloc[0].to_dict())

        return {"designs": results}

    except Exception as e:
        return {"error": str(e)}


