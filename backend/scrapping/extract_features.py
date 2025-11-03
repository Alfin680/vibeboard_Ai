import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import pandas as pd
from tqdm import tqdm
import requests
from io import BytesIO
import numpy as np
import os

# Paths
input_csv = "data/cleaned_designs.csv"
output_npy = "data/features.npy"
output_csv = "data/featured_designs.csv"

# Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Load dataset
df = pd.read_csv(input_csv)
print(f"Processing {len(df)} designs...")

embeddings = []

for _, row in tqdm(df.iterrows(), total=len(df)):
    try:
        image_url = row["image"]
        text = f"{row.get('title','')} {row.get('tags','')} {row.get('author','')}"

        # Download image
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert("RGB")

        inputs = processor(text=[text], images=image, return_tensors="pt", padding=True).to(device)
        outputs = model(**inputs)

        # Combine text + image embeddings
        img_emb = outputs.image_embeds.detach().cpu().numpy()[0]
        txt_emb = outputs.text_embeds.detach().cpu().numpy()[0]
        combined = np.concatenate([img_emb, txt_emb])
        embeddings.append(combined)

    except Exception as e:
        print(f"⚠️ Skipping {row.get('title','Unknown')} — {e}")
        embeddings.append(np.zeros(1024))

# Save embeddings
embeddings = np.array(embeddings)
np.save(output_npy, embeddings)
df.to_csv(output_csv, index=False)

print(f"✅ Saved {embeddings.shape[0]} embeddings ({embeddings.shape[1]}-D) to {output_npy}")
print(f"✅ Updated CSV saved to {output_csv}")
