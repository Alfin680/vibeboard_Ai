import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

# Load data
data_path = os.path.join("data", "cleaned_designs.csv")
embed_path = os.path.join("data", "embeddings_cache.json")

print("🔍 Loading cleaned data...")
df = pd.read_csv(data_path)

print("🧠 Loading embeddings...")
with open(embed_path, "r") as f:
    embeddings = json.load(f)

# Convert dict of embeddings to array
embeddings_matrix = np.array(list(embeddings.values()))
urls = list(embeddings.keys())

# Ensure alignment with dataset
df = df[df["url"].isin(urls)].reset_index(drop=True)
embeddings_matrix = np.array([embeddings[url] for url in df["url"]])

# Cluster using K-Means
n_clusters = 8  # you can tune this
print(f"🎨 Clustering {len(df)} designs into {n_clusters} groups...")
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df["cluster"] = kmeans.fit_predict(embeddings_matrix)

# Save clustered data
clustered_csv = os.path.join("data", "clustered_designs.csv")
df.to_csv(clustered_csv, index=False)
print(f"✅ Clustered dataset saved → {clustered_csv}")

# Build similarity index (cosine similarity)
print("🔗 Calculating similarity matrix...")
similarity_matrix = cosine_similarity(embeddings_matrix)

# Save similarity results
similarity_output = os.path.join("data", "similarity_matrix.npy")
np.save(similarity_output, similarity_matrix)
print(f"💾 Similarity matrix saved → {similarity_output}")

print("🎉 Clustering + similarity indexing complete!")
