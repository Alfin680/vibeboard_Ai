# from flask import Flask, jsonify, request
# import pandas as pd
# import numpy as np
# import json
# from sklearn.metrics.pairwise import cosine_similarity
# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# # Initialize Flask

# load_dotenv()
# app = Flask(__name__)

# # Load Data
# DATA_PATH = "data/clustered_designs.csv"
# SIMILARITY_PATH = "data/similarity_matrix.npy"
# EMBEDDINGS_PATH = "data/embeddings_cache.json"

# df = pd.read_csv(DATA_PATH)
# similarity_matrix = np.load(SIMILARITY_PATH)
# with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
#     embeddings_dict = json.load(f)

# # Initialize OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# # ------------------------ ROUTES ------------------------

# @app.route("/")
# def home():
#     return jsonify({"message": "VibeBoard API is running!"})


# @app.route("/designs", methods=["GET"])
# def get_designs():
#     page = int(request.args.get("page", 1))
#     per_page = int(request.args.get("per_page", 20))
#     start = (page - 1) * per_page
#     end = start + per_page

#     data = df.iloc[start:end].to_dict(orient="records")
#     return jsonify({
#         "page": page,
#         "total": len(df),
#         "data": data
#     })


# @app.route("/design/<int:index>", methods=["GET"])
# def get_design(index):
#     if index < 0 or index >= len(df):
#         return jsonify({"error": "Invalid index"}), 404

#     return jsonify(df.iloc[index].to_dict())


# @app.route("/related/<int:index>", methods=["GET"])
# def get_related(index):
#     if index < 0 or index >= len(df):
#         return jsonify({"error": "Invalid index"}), 404

#     sims = similarity_matrix[index]
#     top_indices = np.argsort(-sims)[1:6]  # top 5 excluding itself
#     related = df.iloc[top_indices][["title", "url", "tags", "image_url"]]
#     return jsonify(related.to_dict(orient="records"))


# @app.route("/search", methods=["POST"])
# def search_designs():
#     data = request.get_json()
#     query = data.get("query", "").strip()
#     if not query:
#         return jsonify({"error": "Missing query"}), 400

#     # Generate embedding for query
#     try:
#         response = client.embeddings.create(
#             model="text-embedding-3-large",
#             input=query
#         )
#         query_emb = np.array(response.data[0].embedding)
#     except Exception as e:
#         return jsonify({"error": f"Embedding generation failed: {e}"}), 500

#     # Compare to all embeddings
#     urls = list(embeddings_dict.keys())
#     embed_matrix = np.array([embeddings_dict[url] for url in urls])
#     similarities = cosine_similarity([query_emb], embed_matrix)[0]
#     top_indices = np.argsort(-similarities)[:10]

#     results = []
#     for i in top_indices:
#         row = df[df["url"] == urls[i]]
#         if not row.empty:
#             results.append(row.iloc[0].to_dict())

#     return jsonify(results)


# @app.route("/clusters", methods=["GET"])
# def get_clusters():
#     clusters = df["cluster"].unique()
#     cluster_summary = []

#     for c in clusters:
#         subset = df[df["cluster"] == c].head(3)  # top 3 samples per cluster
#         cluster_summary.append({
#             "cluster": int(c),
#             "count": len(df[df["cluster"] == c]),
#             "examples": subset[["title", "url", "tags", "image_url"]].to_dict(orient="records")
#         })

#     return jsonify(cluster_summary)


# # ------------------------ MAIN ------------------------
# if __name__ == "__main__":
#     app.run(debug=True)
import os
import json
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --- Initialize App ---
app = FastAPI(title="VibeBoard API", version="1.0")

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this later to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- File Paths ---
DATA_PATH = "data/clustered_designs.csv"
EMBED_PATH = "data/embeddings_cache.json"
SIMILARITY_PATH = "data/similarity_matrix.npy"

# --- Load Data ---
print("Loading dataset and embeddings...")
df = pd.read_csv(DATA_PATH)

with open(EMBED_PATH, "r", encoding="utf-8") as f:
    stored_embeddings = json.load(f)

urls = list(stored_embeddings.keys())
emb_matrix = np.array(list(stored_embeddings.values()))

# Load local model for query embeddings
model = SentenceTransformer("BAAI/bge-base-en")

print(f"✅ Loaded {len(emb_matrix)} embeddings.")


# --- API Endpoints ---

@app.get("/")
def root():
    return {"status": "VibeBoard API is running"}


@app.get("/search")
def search(q: str = Query(..., description="Search query")):
    """Semantic search based on query text."""
    if not q.strip():
        return {"error": "Query cannot be empty"}

    query_emb = model.encode(q, normalize_embeddings=True).reshape(1, -1)
    sims = cosine_similarity(emb_matrix, query_emb).flatten()

    top_idx = sims.argsort()[-10:][::-1]
    top_urls = [urls[i] for i in top_idx]
    results = df[df["url"].isin(top_urls)].to_dict(orient="records")
    return {"results": results}


@app.get("/designs")
def get_designs():
    """Return all designs."""
    return {"designs": df.to_dict(orient="records")}


@app.get("/clusters")
def get_clusters():
    """Return sample designs from each cluster."""
    clusters = df.groupby("cluster").apply(lambda x: x.sample(min(10, len(x)))).reset_index(drop=True)
    return {"clusters": clusters.to_dict(orient="records")}


@app.get("/related")
def get_related(url: str = Query(..., description="Design URL")):
    """Return related designs based on cosine similarity."""
    if url not in stored_embeddings:
        return {"error": "Invalid or missing URL"}

    idx = urls.index(url)
    sims = cosine_similarity([emb_matrix[idx]], emb_matrix).flatten()
    top_idx = sims.argsort()[-6:][::-1][1:]
    related = df[df["url"].isin([urls[i] for i in top_idx])].to_dict(orient="records")
    return {"related": related}
