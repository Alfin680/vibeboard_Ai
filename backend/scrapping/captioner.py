import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI

# =====================================
# CONFIG
# =====================================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "cleaned_designs.csv"      # input: source,title,author,price,tags,image,url
OUTPUT_FILE = DATA_DIR / "captioned_designs.csv"   # output: adds ai_caption + palette + colors

# =====================================
# PROMPT TEMPLATE
# =====================================
CAPTIONER_PROMPT = """
You are a senior product designer and visual stylist.

Your task: analyse a website’s visual and textual hints, then output a JSON object describing its overall mood, layout, and colour system.

---

### INPUT
Source: {source}
Title: {title}
Author: {author}
Price: {price}
Scraped tags / description: {tags}
Preview image URL: {image}
Page URL: {url}

Optional visual metadata (may be blank):
Primary color HEX (from deterministic extraction): {primary_hex}
Detected elements: {element_detections}
CLIP tags: {clip_tags}
Layout hint: {layout_hint}
Image confidence (0.0–1.0): {image_confidence}

---

### OUTPUT FORMAT
Return *only* a valid JSON object with this schema:

{{
  "ai_caption": "string (<=120 chars)",
  "primary_hex": "#hex or empty string",
  "primary_descriptor": "string (e.g., 'muted blue','warm beige','bright coral')",
  "ai_palette": ["#hex1","#hex2","#hex3","#hex4"],
  "image_confidence": 0.0
}}

---

### RULES
1. Evidence-first. Use provided inputs; prefer deterministic primary_hex if available.
2. Caption style: ≤120 chars, factual, designer voice. Mention mood, layout, color tone, and one design element if possible.
3. Color logic:
   - If primary_hex exists → treat as dominant; derive descriptor from tone.
   - If not → infer up to 4 hex colors & one descriptor, use stable, web-safe hexes.
4. Avoid vague or marketing terms ("beautiful", "possibly").
5. Confidence:
   - Start from input or 0.5 if blank.
   - +0.15 if primary_hex provided.
   - +0.10 if 2+ detected elements or CLIP cues.
   - -0.15 if both color and elements missing.
   - Clamp to [0.0,1.0], round to 2 decimals.
6. Output one valid JSON object, no commentary.

---

### EXAMPLE
Input →
title: "Luna Finance", primary_hex: "#1e3a8a", layout_hint: "dashboard",
tags: "Finance, SaaS", image_confidence: 0.9

Output →
{{
 "ai_caption": "Calm fintech dashboard with muted blue palette and structured card layout.",
 "primary_hex": "#1e3a8a",
 "primary_descriptor": "muted blue",
 "ai_palette": ["#1e3a8a","#e8eef6","#ffffff"],
 "image_confidence": 0.90
}}
"""

# =====================================
# CAPTIONER FUNCTION
# =====================================
def generate_caption(data):
    try:
        prompt = CAPTIONER_PROMPT.format(
            source=data.get("source", ""),
            title=data.get("title", ""),
            author=data.get("author", ""),
            price=data.get("price", ""),
            tags=data.get("tags", ""),
            image=data.get("image", ""),
            url=data.get("url", ""),
            primary_hex=data.get("primary_hex", ""),
            element_detections=data.get("element_detections", ""),
            clip_tags=data.get("clip_tags", ""),
            layout_hint=data.get("layout_hint", ""),
            image_confidence=data.get("image_confidence", "0.5")
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.1,
            max_output_tokens=250
        )

        result = response.output_text.strip()

        # try to parse valid JSON
        try:
            parsed = json.loads(result)
            return parsed
        except json.JSONDecodeError:
            print("⚠ JSON parse error, raw output:", result)
            return {
                "ai_caption": "",
                "primary_hex": "",
                "primary_descriptor": "",
                "ai_palette": "[]",
                "image_confidence": 0.0
            }

    except Exception as e:
        print(f"⚠ Error generating caption: {e}")
        return {
            "ai_caption": "",
            "primary_hex": "",
            "primary_descriptor": "",
            "ai_palette": "[]",
            "image_confidence": 0.0
        }

# =====================================
# MAIN PIPELINE
# =====================================
def main():
    print("🎨 Generating AI captions + color palettes...")
    df = pd.read_csv(INPUT_FILE)
    captions, prim_hex, prim_desc, palettes, confs = [], [], [], [], []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        output = generate_caption(row)

        captions.append(output.get("ai_caption", ""))
        prim_hex.append(output.get("primary_hex", ""))
        prim_desc.append(output.get("primary_descriptor", ""))
        palettes.append(json.dumps(output.get("ai_palette", [])))
        confs.append(output.get("image_confidence", 0.0))

        time.sleep(0.5)  # gentle rate limit

    df["ai_caption"] = captions
    df["primary_hex"] = prim_hex
    df["primary_descriptor"] = prim_desc
    df["ai_palette"] = palettes
    df["image_confidence"] = confs

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved captioned dataset → {OUTPUT_FILE}")
    print(f"✅ Total processed: {len(df)} designs")

if __name__ == "__main__":
    main()