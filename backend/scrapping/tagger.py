import os
import pandas as pd
import json
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import time

# =========================
# SETTINGS
# =========================
load_dotenv()
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "captioned_designs.csv"   # input from captioner
OUTPUT_FILE = DATA_DIR / "tagged_designs.csv"     # enriched output

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# ENHANCED PROMPT (with colors)
# =========================
TAGGER_PROMPT = """
You are an expert visual curator and design analyst.
Your job is to analyze a website design and produce structured metadata capturing its mood, purpose, and style.

Use text metadata and color information to describe the design accurately.

---

INPUT:
Source: {source}
Title: {title}
Caption: {caption}
Raw Tags: {tags_raw}
Dominant Colors (HEX): {colors}
Layout Hint: {layout_hint}
Optional Color Descriptors: {color_descriptors}

---

TASK:
Return a valid JSON object (no commentary).

{{
  "ai_caption": "string (<=120 chars)",
  "ai_tags": ["tag1", "tag2", "tag3"],
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "layout": "string",
  "font_style": "string",
  "aesthetic_style": "string",
  "confidence": 0.0
}}

CONTROLLED VOCABULARY:
["minimal", "playful", "bold", "luxury", "calm", "vibrant", "organic", "techy",
"modern", "retro", "premium", "elegant", "dark", "colorful", "friendly",
"editorial", "artistic", "geometric", "warm", "cool", "spacious", "compact",
"creative", "corporate", "youthful", "clean", "futuristic", "professional",
"soft", "dynamic", "trustworthy", "high-contrast", "monochrome", "neon",
"warm-tone", "cool-tone", "gradient", "flat", "3d", "illustrative", "experimental"]

---

EXAMPLES:
Input →
Title: "Luna Finance"
Caption: "Calm fintech dashboard with muted blue and white palette."
Colors: ["#e8eef6", "#1e3a8a", "#ffffff"]
Layout Hint: "Dashboard"
Raw Tags: "Finance, SaaS"

Output →
{{
  "ai_caption": "Calm, professional fintech dashboard with muted blue tones.",
  "ai_tags": ["calm", "minimal", "professional", "finance"],
  "dominant_colors": ["#e8eef6", "#1e3a8a", "#ffffff"],
  "layout": "dashboard",
  "font_style": "sans-serif",
  "aesthetic_style": "apple-style",
  "confidence": 0.94
}}

Return JSON only.
"""

# =========================
# TAG GENERATION FUNCTION
# =========================
def generate_tags(title, caption, source, tags_raw, colors, layout_hint, color_descriptors):
    try:
        prompt = TAGGER_PROMPT.format(
            title=title or "",
            caption=caption or "",
            source=source or "",
            tags_raw=tags_raw or "",
            colors=colors or "[]",
            layout_hint=layout_hint or "unknown",
            color_descriptors=color_descriptors or "",
        )

        response = client.responses.create(
            model="gpt-4.1",
            input=prompt,
            temperature=0.0,
            max_output_tokens=512
        )

        output = response.output_text.strip()
        json_str = output[output.find("{"):output.rfind("}") + 1]
        parsed = json.loads(json_str)
        return parsed

    except Exception as e:
        title_safe = str(title) if not isinstance(title, float) else ""
        print(f"⚠ Error tagging {title_safe[:30]}: {e}")
        return {
            "ai_caption": "",
            "ai_tags": [],
            "dominant_colors": [],
            "layout": "unknown",
            "font_style": "unknown",
            "aesthetic_style": "unknown",
            "confidence": 0.0
        }

# =========================
# MAIN SCRIPT
# =========================
def main():
    print("🏷 Tagging designs with enhanced metadata...")
    df = pd.read_csv(INPUT_FILE)
    results = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        title = str(row.get("title", "") or "")
        caption = str(row.get("ai_caption", "") or "")
        source = str(row.get("source", "") or "")
        tags_raw = str(row.get("tags", "") or "")
        colors = str(row.get("dominant_colors", "") or "")
        layout_hint = str(row.get("layout", "unknown") or "unknown")
        color_descriptors = str(row.get("color_descriptors", "") or "")

        result = generate_tags(title, caption, source, tags_raw, colors, layout_hint, color_descriptors)
        results.append(result)
        time.sleep(0.4)  # small delay to avoid rate limits

    # Flatten structured results into DataFrame
    df["ai_caption"] = [r.get("ai_caption", "") for r in results]
    df["ai_tags"] = [", ".join(r.get("ai_tags", [])) for r in results]
    df["layout"] = [r.get("layout", "unknown") for r in results]
    df["font_style"] = [r.get("font_style", "unknown") for r in results]
    df["aesthetic_style"] = [r.get("aesthetic_style", "unknown") for r in results]
    df["confidence"] = [r.get("confidence", 0.0) for r in results]

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved tagged dataset → {OUTPUT_FILE}")
    print(f"✅ Total designs tagged: {len(df)}")

if __name__ == "__main__":
    main()
