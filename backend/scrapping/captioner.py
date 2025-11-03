import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import time
import json

# =========================
# SETTINGS
# =========================
load_dotenv()
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "combined_designs.csv"         # input file (has title, caption, image_url)
OUTPUT_FILE = DATA_DIR / "captioned_designs.csv"  # output file (will include ai_caption)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# PROMPT TEMPLATE
# =========================
CAPTION_PROMPT = """
You are a concise design editor. 
Given metadata and visual hints, output a single-sentence caption (<=120 chars) describing mood, color tone, and layout. 
Keep it editorial and neutral. Avoid marketing words like 'beautiful' or 'stunning'. 
Output only the caption.

Title: {title}
Scraped caption: {caption}
Image hints: {image_hints}
Colors: {colors}
Layout: {layout_hint}

Examples:
1️⃣ "Soft minimal layout with pale beige tones and generous white space."
2️⃣ "Dark fintech dashboard with neon-blue accents and precise data grids."
3️⃣ "Playful landing with rounded shapes, vibrant gradients, and bold CTAs."

Now produce the caption:
"""

# =========================
# CAPTION GENERATION FUNCTION
# =========================
def generate_caption(title, caption, image_hints, colors, layout_hint):
    """
    Generate a concise design caption.
    """
    try:
        prompt = CAPTION_PROMPT.format(
            title=title or "",
            caption=caption or "",
            image_hints=image_hints or "",
            colors=colors or "",
            layout_hint=layout_hint or "unknown"
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.2,
        )

        result = response.output_text.strip()
        return result

    except Exception as e:
        print(f"⚠ Error generating caption: {e}")
        return ""

# =========================
# MAIN SCRIPT
# =========================
def main():
    print("✍ Generating AI captions...")
    df = pd.read_csv(INPUT_FILE)
    captions = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        title = row.get("title", "")
        caption = row.get("caption", "")
        image_hints = row.get("image_hints", "")      # e.g., extracted CLIP tags or empty
        colors = row.get("dominant_colors", "")       # e.g., ["#f0f0f0","#1a1a1a"]
        layout_hint = row.get("layout", "unknown")

        ai_caption = generate_caption(title, caption, image_hints, colors, layout_hint)
        captions.append(ai_caption)
        time.sleep(0.3)  # simple rate limit

    df["ai_caption"] = captions
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved captioned dataset → {OUTPUT_FILE}")
    print(f"✅ Total designs captioned: {len(df)}")

if __name__ == "__main__":
    main()