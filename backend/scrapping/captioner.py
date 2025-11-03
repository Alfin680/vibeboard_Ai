import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv



# =========================
# SETTINGS
# =========================
load_dotenv()
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "combined_designs.csv"
OUTPUT_FILE = DATA_DIR / "captioned_designs.csv"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# CAPTION GENERATION
# =========================
def generate_caption(title, image_url, source):
    """
    Generate a short human-like caption describing a website design.
    """
    try:
        prompt = f"""
        You are an expert website design critic. Write a single creative sentence (max 25 words)
        describing the vibe and style of this website design.
        Website source: {source}
        Title: {title}
        Image: {image_url}
        Example captions:
        - "A sleek portfolio site blending minimal typography with vivid gradients."
        - "A bold eCommerce layout with smooth transitions and a modern aesthetic."
        - "A serene landing page design focused on calm colors and whitespace."
        Now write your caption:
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        caption = response.output_text.strip()
        return caption

    except Exception as e:
        print(f"⚠️ Error generating caption: {e}")
        return ""


# =========================
# MAIN SCRIPT
# =========================
def main():
    print("🚀 Generating captions using OpenAI...")
    df = pd.read_csv(INPUT_FILE)
    captions = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        title = row.get("title", "")
        image = row.get("image", "")
        source = row.get("source", "")
        caption = generate_caption(title, image, source)
        captions.append(caption)

    df["ai_caption"] = captions
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved captioned dataset → {OUTPUT_FILE}")
    print(f"✅ Total captions generated: {len(df)}")


if __name__ == "__main__":
    main()
