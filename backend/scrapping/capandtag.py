# test_run_2rows.py
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT = "data/visual_features.csv"
OUTPUT = "data/test_output.csv"

MODEL = "gpt-4.1-mini"

df = pd.read_csv(INPUT).head(2)   # FIRST 2 ONLY

captions, tags = [], []

for _, row in df.iterrows():
    title = str(row.get("title",""))
    primary_hex = str(row.get("primary_hex",""))
    colors_arr = str(row.get("dominant_colors",""))
    primary_weight = float(row.get("color_weights", "{}").strip("{}").split(":")[-1]) if row.get("color_weights") else 0.0
    elements = str(row.get("elements",""))
    mood = str(row.get("mood_keywords",""))
    src = str(row.get("source",""))

    prompt = f"""
You are an expert UI design captioner.

IMPORTANT THRESHOLDS:
- MIN_AREA_FRAC = 0.12
- PRIMARY_WEIGHT_THRESHOLD = 0.18
- WHITE_DOMINANCE_PROMOTE_THRESHOLD = 0.45
- TOP_N_COLORS = 2

COLOR RULE:
If primary_hex exists + its pixel weight >= PRIMARY_WEIGHT_THRESHOLD → use that color in caption.
If primary_hex is near-white (#fafafa, #ffffff, #fdfdfd, etc) AND a secondary dominant color exists → use the secondary color.
If colors are uncertain (<0.12 weight) → describe as "neutral" / "dark" / "light" only (no hex mention).

TASKS:
1) CAPTION (max 120 chars): describe layout feel + main color tone + 1 structural design cue (only 1 sentence)
2) TAGS: 5–7 lowercase comma-separated tags

INPUT:
Source: {src}
Title: {title}
primary_hex: {primary_hex}
dominant_colors: {colors_arr}
ui elements: {elements}
mood hints: {mood}
primary_weight: {primary_weight}

OUTPUT FORMAT YOU MUST FOLLOW EXACTLY:

CAPTION: <your caption>
TAGS: tag1, tag2, tag3, tag4, tag5, tag6
"""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0.55
    )

    text = r.choices[0].message.content.strip()
    lines = text.split("\n")
    cap = lines[0].replace("CAPTION:","").strip()
    tg = lines[1].replace("TAGS:","").strip()

    captions.append(cap)
    tags.append(tg)

df["ai_caption"] = captions
df["ai_tags"] = tags
df.to_csv(OUTPUT,index=False)
print("✅ test done → data/test_output.csv")
