# import os
# import json
# import pandas as pd
# from openai import OpenAI
# from tqdm import tqdm
# from dotenv import load_dotenv
# load_dotenv()


# # Initialize OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # File paths
# INPUT_CSV = "data/ai_captions_tags_clean.csv"
# OUTPUT_JSON = "data/embeddings_cache.json"

# def build_text_representation(row):
#     """Combine text attributes into one descriptive string."""
#     text_parts = [
#         row.get("caption", ""),
#         row.get("tags", ""),
#         row.get("elements", ""),
#         row.get("mood_keywords", ""),
#         row.get("primary_descriptor", ""),
#     ]
#     return " | ".join([t for t in text_parts if pd.notna(t)])

# def main():
#     print(" Generating embeddings for tagged dataset...")

#     df = pd.read_csv(INPUT_CSV)
#     embeddings = {}

#     for _, row in tqdm(df.iterrows(), total=len(df)):
#         url = row.get("url")
#         if not url or pd.isna(url):
#             continue

#         text = build_text_representation(row)
#         if not text.strip():
#             continue

#         try:
#             response = client.embeddings.create(
#                 model="text-embedding-3-large",
#                 input=text
#             )
#             embeddings[url] = response.data[0].embedding
#         except Exception as e:
#             print(f" Error embedding {url}: {e}")

#     # Save embeddings
#     os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
#     with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
#         json.dump(embeddings, f)

#     print(f"Saved {len(embeddings)} embeddings → {OUTPUT_JSON}")

# if __name__ == "__main__":
#     main()


import os
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths
INPUT_CSV = "data/ai_captions_tags_clean.csv"
OUTPUT_JSON = "data/embeddings_cache.json"

def build_text_representation(row):
    """Combine text attributes into one descriptive string."""
    text_parts = [
        row.get("caption", ""),
        row.get("tags", ""),
        row.get("elements", ""),
        row.get("mood_keywords", ""),
        row.get("primary_descriptor", "")
    ]
    return " | ".join([t for t in text_parts if pd.notna(t) and str(t).strip()])

def main():
    print("Generating OpenAI embeddings for tagged dataset...")

    df = pd.read_csv(INPUT_CSV)
    embeddings = {}

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Embedding rows"):
        url = row.get("url")
        if not url or pd.isna(url):
            continue

        text = build_text_representation(row)
        if not text.strip():
            continue

        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            embeddings[url] = response.data[0].embedding
        except Exception as e:
            print(f"Error embedding {url}: {e}")

    # Save embeddings as JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(embeddings, f)

    print(f"Saved {len(embeddings)} embeddings -> {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
