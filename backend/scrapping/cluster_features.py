import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# File paths
CLEAN_CSV = "data/ai_captions_tags_clean.csv"
EMBED_JSON = "data/embeddings_cache.json"
OUTPUT_CLUSTERED = "data/clustered_designs.csv"
OUTPUT_SIMILARITY = "data/similarity_matrix.npy"

def main():
    print("Loading embeddings and dataset...")

    # Load CSV + embeddings
    df = pd.read_csv(CLEAN_CSV)
    with open(EMBED_JSON, "r", encoding="utf-8") as f:
        embeddings = json.load(f)

    # Keep only rows with embeddings
    df = df[df["url"].isin(embeddings.keys())].reset_index(drop=True)
    if df.empty:
        raise ValueError("No matching URLs found between CSV and embeddings JSON.")

    matrix = np.array([embeddings[url] for url in df["url"]])

    print(f"Clustering {len(matrix)} designs...")

    # Run KMeans clustering
    n_clusters = 8
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(matrix)

    # Compute cosine similarity
    print("Calculating similarity matrix...")
    similarity = cosine_similarity(matrix)

    # Ensure output folder exists
    os.makedirs(os.path.dirname(OUTPUT_CLUSTERED), exist_ok=True)

    # Save clustered dataset and similarity matrix
    df.to_csv(OUTPUT_CLUSTERED, index=False)
    np.save(OUTPUT_SIMILARITY, similarity)

    print(f"Clustered dataset saved -> {OUTPUT_CLUSTERED}")
    print(f"Similarity matrix saved -> {OUTPUT_SIMILARITY}")
    print("Feature extraction complete.")

if __name__ == "__main__":
    main()
