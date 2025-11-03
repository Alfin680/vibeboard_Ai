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
OUTPUT_FILE = DATA_DIR / "captioned_designs.csv"       # output file (will include ai_caption + ai_palette)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# PROMPT TEMPLATES
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

PALETTE_PROMPT = """
You are a design color expert.
Given the following metadata, identify 3-5 dominant web-safe color hex codes that would likely represent the design's mood.
Return ONLY a JSON array of hex codes (no extra text).

Title: {title}
Scraped caption: {caption}
Image hints: {image_hints}
"""

# =========================
# FUNCTIONS
# =========================
def generate_caption(title, caption, image_hints, colors, layout_hint):
    """Generate a concise design caption."""
    try:
        prompt = CAPTION_PROMPT.format(
            title=title or "",
            caption=caption or "",
            image_hints=image_hints or "",
            colors=colors or "",
            layout_hint=layout_hint or "unknown"
        )

        response = client.responses.create(
            model="gpt-4.1",   # upgraded model
            input=prompt,
            temperature=0.2,
        )

        result = response.output_text.strip()
        return result

    except Exception as e:
        print(f"⚠ Error generating caption: {e}")
        return ""


def generate_palette(title, caption, image_hints):
    """Generate color palette as a JSON array of hex codes."""
    try:
        prompt = PALETTE_PROMPT.format(
            title=title or "",
            caption=caption or "",
            image_hints=image_hints or ""
        )

        response = client.responses.create(
            model="gpt-4.1",   # upgraded model
            input=prompt,
            temperature=0.3,
        )

        result = response.output_text.strip()

        # Validate palette
        try:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return json.dumps(parsed)
            else:
                return "[]"
        except:
            return "[]"

    except Exception as e:
        print(f"⚠ Error generating palette: {e}")
        return "[]"


# =========================
# MAIN SCRIPT
# =========================
def main():
    print("🎨 Generating AI captions and color palettes...")
    df = pd.read_csv(INPUT_FILE)
    ai_captions, ai_palettes = [], []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        title = row.get("title", "")
        caption = row.get("caption", "")
        image_hints = row.get("image_hints", "")
        colors = row.get("dominant_colors", "")
        layout_hint = row.get("layout", "unknown")

        ai_caption = generate_caption(title, caption, image_hints, colors, layout_hint)
        ai_palette = generate_palette(title, caption, image_hints)

        ai_captions.append(ai_caption)
        ai_palettes.append(ai_palette)

        time.sleep(0.4)  # simple rate limit

    df["ai_caption"] = ai_captions
    df["ai_palette"] = ai_palettes

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved captioned + palette dataset → {OUTPUT_FILE}")
    print(f"✅ Total designs processed: {len(df)}")

if __name__ == "__main__":
    main()
