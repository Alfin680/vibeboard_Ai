import os
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()  # load API keys from .env

def generate_embeddings(csv_path="data/designs.csv", output_path="data/embeddings_cache.json"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    df = pd.read_csv(csv_path)
    embeddings_cache = {}

    print("🚀 Generating embeddings...")
    for i, row in tqdm(df.iterrows(), total=len(df)):
        text = f"{row['title']} - {row['description']} - {row['vibe_words']}"
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        vector = response.data[0].embedding
        embeddings_cache[row['title']] = vector

    # Save embeddings locally
    with open(output_path, "w") as f:
        json.dump(embeddings_cache, f)

    print(f"✅ Saved embeddings to {output_path}")

if __name__ == "__main__":
    generate_embeddings()