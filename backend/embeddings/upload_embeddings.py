import os
import json
from dotenv import load_dotenv
from backend.db.pinecone_client import get_pinecone_index

load_dotenv()

def upload_embeddings_from_cache(cache_path="data/embeddings_cache.json"):
    index = get_pinecone_index()

    with open(cache_path, "r") as f:
        embeddings_cache = json.load(f)

    vectors = []
    for title, vector in embeddings_cache.items():
        vectors.append({
            "id": title,
            "values": vector,
            "metadata": {"title": title}
        })

    index.upsert(vectors)
    print("✅ Uploaded embeddings to Pinecone!")


if __name__ == "__main__":
    upload_embeddings_from_cache()
