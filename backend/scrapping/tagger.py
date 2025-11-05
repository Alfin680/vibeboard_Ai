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
Your goal is to analyze a website design and output structured metadata that captures its mood, style, layout, and core aesthetic qualities.

Always reason from evidence (inputs provided), not imagination. 
Return clean, valid JSON only — no commentary, no explanation.

---

### INPUT
Source: {source}
Title: {title}
Author: {author}
Price: {price}
Scraped Tags: {tags}
Image URL: {image}
Page URL: {url}

AI Caption: {ai_caption}
Primary Color HEX: {primary_hex}
Primary Color Descriptor: {primary_descriptor}
Detected Elements: {element_detections}
CLIP Tags: {clip_tags}
Layout Hint: {layout_hint}
Image Confidence: {image_confidence}

---

### OUTPUT FORMAT
{{
  "ai_tags": ["tag1", "tag2", "tag3"],
  "layout": "string",
  "font_style": "string",
  "aesthetic_style": "string",
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "confidence": 0.0
}}

---

### CONTROLLED VOCABULARIES
ai_tags:
["minimal","playful","bold","luxury","calm","vibrant","organic","techy",
"modern","retro","premium","elegant","dark","colorful","friendly","editorial",
"artistic","geometric","warm","cool","spacious","compact","creative","corporate",
"youthful","clean","futuristic","professional","soft","dynamic","trustworthy",
"high-contrast","monochrome","neon","warm-tone","cool-tone","gradient","flat","3d",
"illustrative","experimental","glassmorphism","neumorphism","brutalist","modernist",
"minimal-flat","skeuomorphic","dark-mode","light-mode","airy","dense","structured",
"asymmetric","layered","grid-based","card-based","photographic","text-heavy",
"image-heavy","hero-centric","micro-animated","motion-rich","sharp-edged",
"soft-rounded","inviting","serious","energetic","moody","soothing","joyful",
"balanced","premium","casual"]

layout:
["landing","dashboard","portfolio","app","ecommerce","blog","editorial","unknown"]

font_style:
["serif","sans-serif","geometric_sans","display","monospace","unknown"]

aesthetic_style:
["modernist","minimal-flat","editorial","retro","brutalist","luxury","organic",
"glassmorphism","flat","3d","gradient","illustrative","experimental","unknown"]

---

### SMARTER RULES (Follow EXACTLY)

1. *Evidence-first:*  
   Base every decision on one or more of: ai_caption, primary_descriptor, detected_elements, clip_tags, layout_hint, or scraped tags.  
   Do NOT invent visuals or emotional qualities that aren’t present in the inputs.

2. *Controlled vocab only:*  
   Use only terms from the vocabularies above.  
   If none apply, output "unknown" or an empty list.

3. *Derive 3 vibe tags:*  
   - Combine mood (calm, bold, playful), density (spacious, compact), and visual tone (flat, gradient, dark-mode).  
   - Rank candidate tags by relevance found in ai_caption, primary_descriptor, or detected_elements.  
   - Output up to 3.  
   - Avoid redundancy (e.g., “calm” + “soothing”).

4. *Layout logic:*  
   - If layout_hint provided → use it directly.  
   - If not, infer from ai_caption (e.g., mentions of “dashboard”, “portfolio”).  
   - Otherwise → "unknown".

5. *Font style mapping:*  
   - "elegant", "editorial", "serif" → "serif"  
   - "geometric", "clean", "modern", "sans" → "geometric_sans"  
   - "display", "bold headings", "hero type" → "display"  
   - else "unknown"

6. *Aesthetic style mapping:*  
   - "gradient", "vibrant", "neon" → "gradient"  
   - "glass", "blur", "translucent" → "glassmorphism"  
   - "soft shadow", "raised", "rounded" → "neumorphism"  
   - "asymmetric", "collage", "editorial" → "editorial"  
   - "high contrast", "brutal", "bold typography" → "brutalist"  
   - "flat", "minimal", "clean layout" → "minimal-flat"  
   - else "unknown"

7. *Dominant colors:*  
   - Use the provided HEX values if available.  
   - If missing, infer 2–3 hex approximations from primary_descriptor using deterministic tone-color lookup (e.g., “muted blue” → #1e3a8a, #e8eef6, #ffffff).

8. *Confidence scoring (0.0–1.0):*  
   - Start from image_confidence value.  
   - +0.15 if caption and chosen tags clearly align.  
   - +0.10 if detected_elements reinforce tag choice.  
   - −0.20 if key visual signals are missing or unclear.  
   - Clamp between 0.0–1.0, round to 2 decimals.

9. *Output validation:*  
   - JSON only (no quotes, commentary, or prose).  
   - Every key must exist.  
   - All values must match vocabulary or be "unknown".  
   - If confidence < 0.5, output remains valid but considered low certainty.

10. *Deterministic fallback:*  
   - When uncertain, use "unknown".  
   - Consistency > creativity.  
   - Avoid guessing or using vague words.

---

### EXAMPLES

Input →
AI Caption: "Playful SaaS landing with bright coral CTA and expressive hero illustration."
Primary Color HEX: "#ff6b6b"
Primary Descriptor: "bright coral"
Layout Hint: "landing"
Detected Elements: ["rounded_buttons","cta_button","hero_illustration"]

Output →
{{
  "ai_tags": ["playful","vibrant","modern"],
  "layout": "landing",
  "font_style": "display",
  "aesthetic_style": "gradient",
  "dominant_colors": ["#ff6b6b","#ffffff","#0a0f2b"],
  "confidence": 0.88
}}

---

Now analyze the given inputs and return the JSON object only:
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
            model="gpt-4o-mini",
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
