import os
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests
from io import BytesIO
from tqdm import tqdm

# -------------------------------
# CONFIG
# -------------------------------

# Input CSV (from your scraper)
INPUT_CSV = "backend/scrapping/data/raw_lapaninja_designs.csv"

# Output CSV (with captions)
OUTPUT_CSV = "backend/scrapping/data/tagged_lapaninja_designs.csv"

# Local BLIP model path (offline mode)
# If you downloaded BLIP manually, use the local folder:
MODEL_PATH = "Salesforce/blip-image-captioning-base"

# Or to let Hugging Face download automatically, use this instead:
# MODEL_PATH = "Salesforce/blip-image-captioning-base"

# -------------------------------
# LOAD MODEL
# -------------------------------
print("🚀 Loading BLIP model...")
processor = BlipProcessor.from_pretrained(MODEL_PATH)
model = BlipForConditionalGeneration.from_pretrained(MODEL_PATH)
print("✅ Model loaded successfully!")

# -------------------------------
# LOAD DATA
# -------------------------------
if not os.path.exists(INPUT_CSV):
    raise FileNotFoundError(f"❌ Could not find input CSV at {INPUT_CSV}")

df = pd.read_csv(INPUT_CSV)
print(f"✅ Loaded {len(df)} designs from {INPUT_CSV}")

# Ensure column names
if "image" not in df.columns:
    raise ValueError("❌ No 'image' column found in CSV!")

# -------------------------------
# GENERATE CAPTIONS
# -------------------------------
captions = []

for i, row in tqdm(df.iterrows(), total=len(df)):
    title = row.get("title", "Untitled")
    image_url = row["image"]

    try:
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert("RGB")

        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True)

        print(f"🖼️ {title} → {caption}")
        captions.append(caption)

    except Exception as e:
        print(f"⚠️ Error processing {title}: {e}")
        captions.append("Error")

# -------------------------------
# SAVE OUTPUT
# -------------------------------
df["ai_caption"] = captions
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(f"\n💾 Saved tagged data to {OUTPUT_CSV}")
