# # test_run_2rows.py
# import os
# import pandas as pd
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# INPUT = "data/visual_features.csv"
# OUTPUT = "data/test_output.csv"

# MODEL = "gpt-4.1-mini"

# df = pd.read_csv(INPUT).head(2)   # FIRST 2 ONLY

# captions, tags = [], []

# for _, row in df.iterrows():
#     title = str(row.get("title",""))
#     primary_hex = str(row.get("primary_hex",""))
#     colors_arr = str(row.get("dominant_colors",""))
#     primary_weight = float(row.get("color_weights", "{}").strip("{}").split(":")[-1]) if row.get("color_weights") else 0.0
#     elements = str(row.get("elements",""))
#     mood = str(row.get("mood_keywords",""))
#     src = str(row.get("source",""))

#     prompt = f"""
# You are an expert UI design captioner.

# IMPORTANT THRESHOLDS:
# - MIN_AREA_FRAC = 0.12
# - PRIMARY_WEIGHT_THRESHOLD = 0.18
# - WHITE_DOMINANCE_PROMOTE_THRESHOLD = 0.45
# - TOP_N_COLORS = 2

# COLOR RULE:
# If primary_hex exists + its pixel weight >= PRIMARY_WEIGHT_THRESHOLD → use that color in caption.
# If primary_hex is near-white (#fafafa, #ffffff, #fdfdfd, etc) AND a secondary dominant color exists → use the secondary color.
# If colors are uncertain (<0.12 weight) → describe as "neutral" / "dark" / "light" only (no hex mention).

# TASKS:
# 1) CAPTION (max 120 chars): describe layout feel + main color tone + 1 structural design cue (only 1 sentence)
# 2) TAGS: 5–7 lowercase comma-separated tags

# INPUT:
# Source: {src}
# Title: {title}
# primary_hex: {primary_hex}
# dominant_colors: {colors_arr}
# ui elements: {elements}
# mood hints: {mood}
# primary_weight: {primary_weight}

# OUTPUT FORMAT YOU MUST FOLLOW EXACTLY:

# CAPTION: <your caption>
# TAGS: tag1, tag2, tag3, tag4, tag5, tag6
# """

#     r = client.chat.completions.create(
#         model=MODEL,
#         messages=[{"role":"user","content":prompt}],
#         temperature=0.55
#     )

#     text = r.choices[0].message.content.strip()
#     lines = text.split("\n")
#     cap = lines[0].replace("CAPTION:","").strip()
#     tg = lines[1].replace("TAGS:","").strip()

#     captions.append(cap)
#     tags.append(tg)

# df["ai_caption"] = captions
# df["ai_tags"] = tags
# df.to_csv(OUTPUT,index=False)
# print("✅ test done → data/test_output.csv")
#!/usr/bin/env python3


import os
import json
import re
import time
import argparse
from typing import Optional, Tuple, List, Dict
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Use the same OpenAI client pattern you used earlier:
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


API_MODEL = "gpt-4o-mini"  # change if you want gpt-4.1-mini / other
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment.")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------
# Utility functions
# -------------------------
def normalize_hex(h: Optional[str]) -> str:
    """Return normalized 6-digit hex in lowercase (or empty string)."""
    if not h:
        return ""
    s = str(h).strip().lower().lstrip('"').rstrip('"').lstrip("'").rstrip("'")
    if s.startswith("#"):
        s = s[1:]
    # remove alpha if present (8-digit), keep only last 6 or first 6 depending
    # prefer the first 6 characters
    s = re.sub(r'[^0-9a-f]', '', s)
    if len(s) >= 6:
        s = s[:6]
    s = s.zfill(6)
    return "#" + s


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    if not hex_color:
        return (0, 0, 0)
    c = hex_color.lstrip("#")
    if len(c) != 6:
        c = c.zfill(6)
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return (r, g, b)


def is_near_white(hex_color: str) -> bool:
    r, g, b = hex_to_rgb(hex_color)
    return (r >= 250 and g >= 250 and b >= 250) or (r >= 245 and g >= 245 and b >= 245)


def brightness_category(hex_color: str) -> str:
    """Return 'light', 'dark', or 'neutral' based on mean brightness."""
    r, g, b = hex_to_rgb(hex_color)
    mean = (r + g + b) / 3.0
    if mean >= 200:
        return "light"
    if mean <= 55:
        return "dark"
    return "neutral"


def choose_main_color(dominant_colors: List[str], weights: Dict[str, float]) -> Tuple[str, float]:
    """
    Apply the rule:
    - Normalize hexes
    - If primary is near-white and a second dominant exists, describe the second color instead
    - Return (chosen_hex, its_weight)
    """
    normalized = [normalize_hex(h) for h in dominant_colors if h]
    # get corresponding weights
    if not normalized:
        return ("", 0.0)
    primary = normalized[0]
    primary_weight = weights.get(primary, None)
    # As weights may be in JSON keyed like "#ff00aa" or stored as strings,
    # ensure we normalize weight dict keys:
    norm_weights = {normalize_hex(k): float(v) for k, v in (weights or {}).items() if k}
    if primary_weight is None:
        primary_weight = norm_weights.get(primary, 0.0)
    # if near-white and there is a second color with weight >= threshold, choose second
    if is_near_white(primary) and len(normalized) > 1:
        second = normalized[1]
        second_weight = norm_weights.get(second, 0.0)
        return (second, second_weight)
    return (primary, primary_weight or 0.0)


def load_json_field(field_val):
    """Try to parse a JSON-like field safely; if fails, return sensible empty."""
    if pd.isna(field_val):
        return None
    if isinstance(field_val, (dict, list)):
        return field_val
    s = str(field_val).strip()
    try:
        return json.loads(s)
    except Exception:
        # sometimes field is formatted as '["#fff", "#000"]' or single-quoted. Try replace single with double quotes:
        try:
            return json.loads(s.replace("'", '"'))
        except Exception:
            return None


# -------------------------
# Prompting / validation
# -------------------------
PROMPT_SYSTEM = (
    "You are a senior product designer AI. Given the provided structured fields, generate:\n"
    "1) A single-sentence CAPTION (<=120 characters) describing layout feel, one main color tone, and one visual/structural cue.\n"
    "2) Tags: 5-7 lowercase, comma-separated tags describing style, layout, mood, and color (no title/brand/hex codes).\n\n"
    "Follow the exact output format below (two lines, nothing else):\n"
    "CAPTION: <one-line caption>\n"
    "TAGS: tag1, tag2, tag3, tag4, tag5, tag6\n\n"
    "Output must be factual/designer-tone (no marketing adjectives), single sentence for caption, and obey color rules described below."
)

PROMPT_RULES = (
    "Color logic rules (apply before writing caption):\n"
    " - Only use normalized 6-digit hex colors (#rrggbb). If primary_hex is near-white (#ffffff, #fafafa, #fdfdfd) and a second dominant color exists, describe the second color instead.\n"
    " - If no clear color dominance (chosen color weight < 0.12) use neutral descriptor: 'light', 'dark', or 'neutral' (one word) as main color tone.\n"
    " - Mention at most one main color tone in the caption (e.g., 'bright blue', 'dark muted gray', 'light neutral').\n\n"
    "Caption style rules:\n"
    " - <= 120 characters, single sentence, designer tone, factual and neutral.\n"
    " - Include: overall layout feel + main color tone + one visual/structural cue.\n"
    " - Example caption: \"Clean white landing with soft blue hero and rounded CTAs.\"\n\n"
    "Tags rules:\n"
    " - 5–7 tags, lowercase, comma-separated.\n"
    " - Describe style, layout, mood, and color in simple design vocabulary.\n"
    " - NEVER include title, brand names, or hex codes.\n"
    " - Example tags: minimal, calm, blue, modern, landing, professional\n\n"
    "Return EXACTLY the two lines as shown earlier and nothing else."
)

EXAMPLE_FEW_SHOT = (
    "Example input ->\n"
    "layout_mood: modern\n"
    "elements: rounded buttons, hero image, grid layout\n"
    "chosen_color: #a6c8ff  (weight 0.45)\n"
    "Example output ->\n"
    "CAPTION: Modern grid layout with bright blue hero and rounded buttons.\n"
    "TAGS: modern, grid, bright-blue, rounded-buttons, hero, minimal\n\n"
    "If chosen_color weight < 0.12 then use 'light'/'dark'/'neutral' instead of specific color name.\n"
)


def build_prompt_for_row(row: Dict) -> str:
    dominant_colors = load_json_field(row.get("dominant_colors")) or []
    color_weights_raw = load_json_field(row.get("color_weights")) or {}
    # normalize color_weights: keys might be unnormalized
    norm_weights = {}
    for k, v in color_weights_raw.items():
        nk = normalize_hex(k)
        try:
            norm_weights[nk] = float(v)
        except Exception:
            try:
                norm_weights[nk] = float(str(v).strip())
            except Exception:
                norm_weights[nk] = 0.0

    chosen_hex, chosen_weight = choose_main_color(dominant_colors, norm_weights)

    # Determine color tone string for prompt: if weight < 0.12 use light/dark/neutral else
    if chosen_weight < 0.12 or not chosen_hex:
        # use brightness_category of primary_hex if present; if empty -> neutral
        fallback = brightness_category(chosen_hex) if chosen_hex else "neutral"
        color_label_hint = fallback
    else:
        # convert hex to descriptor like "bright blue" or "dark muted gray"
        # We'll give the normalized hex and descriptor to the model but also precompute a short label.
        # Let the model use descriptor if helpful; still we must ensure it follows one word color tone in caption.
        color_label_hint = chosen_hex  # provide hex, model will map to a descriptor (we also provide descriptor field below)
    # elements/mood provide
    elements_field = row.get("elements") or row.get("elements") or ""
    mood_field = row.get("mood_keywords") or ""
    # primary_descriptor maybe present
    primary_descriptor = row.get("primary_descriptor") or ""

    prompt = (
        PROMPT_SYSTEM + "\n\n"
        + PROMPT_RULES + "\n\n"
        + EXAMPLE_FEW_SHOT + "\n\n"
        + "INPUT FIELDS (do not repeat into caption):\n"
        f"title: {row.get('title','')}\n"
        f"url: {row.get('url','')}\n"
        f"dominant_colors: {dominant_colors}\n"
        f"color_weights: {norm_weights}\n"
        f"primary_hex: {normalize_hex(row.get('primary_hex') or '')}\n"
        f"primary_descriptor: {primary_descriptor}\n"
        f"chosen_color_for_caption_hint: {chosen_hex or ''}\n"
        f"chosen_color_weight: {chosen_weight}\n"
        f"color_hint_word: {color_label_hint}\n"
        f"elements: {elements_field}\n"
        f"mood_keywords: {mood_field}\n"
        f"confidence: {row.get('confidence','')}\n\n"
        "Remember: produce exactly two lines:\nCAPTION: ...\nTAGS: tag1, tag2, tag3, tag4, tag5[, tag6]\n"
    )
    return prompt


CAPTION_TAGS_RE = re.compile(r"^CAPTION:\s*(.+)\s*\nTAGS:\s*(.+)$", re.IGNORECASE | re.DOTALL)


def call_model_and_extract(prompt: str, model: str = API_MODEL, max_retries: int = 2, sleep_between: float = 0.6) -> Tuple[Optional[str], Optional[str]]:
    """
    Calls the OpenAI client, returns (caption, tags) if valid, else (None, None).
    Retries a small number of times if model output is malformed.
    """
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=256
            )
            # extract text
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            # transient error -> retry
            if attempt < max_retries:
                time.sleep(sleep_between * (attempt + 1))
                continue
            return (None, None)

        # validate format strictly
        m = CAPTION_TAGS_RE.match(content)
        if not m:
            # attempt to salvage lines: split by newline and try to find lines starting with CAPTION/TAGS
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            caption_line = None
            tags_line = None
            for ln in lines:
                if ln.lower().startswith("caption:"):
                    caption_line = ln[len("caption:"):].strip()
                if ln.lower().startswith("tags:"):
                    tags_line = ln[len("tags:"):].strip()
            if caption_line and tags_line:
                # basic sanitation
                caption = caption_line
                tags = tags_line
                return (caption, tags)
            # else retry if possible
            if attempt < max_retries:
                time.sleep(sleep_between * (attempt + 1))
                continue
            return (None, None)
        else:
            caption = m.group(1).strip()
            tags = m.group(2).strip()
            return (caption, tags)
    return (None, None)


# -------------------------
# Batch runner
# -------------------------
def process_file(input_csv: str, output_csv: str, start: int = 0, limit: int = 0, model: str = API_MODEL):
    inp_path = Path(input_csv)
    if not inp_path.exists():
        raise FileNotFoundError(f"Input not found: {input_csv}")

    df = pd.read_csv(inp_path)
    n_total = len(df)
    end = n_total if limit <= 0 else min(n_total, start + limit)

    # Track completed URLs to skip duplicates
    done_urls = set()
    out_path = Path(output_csv)
    if out_path.exists():
        prev = pd.read_csv(out_path)
        if "url" in prev.columns:
            done_urls = set(prev["url"].astype(str))
        write_header = False
    else:
        write_header = True

    print(f"Processing rows {start} → {end} (out of {n_total}), skipping {len(done_urls)} already done")

    with open(output_csv, "a", encoding="utf-8", newline="") as f_out:
        for idx in tqdm(range(start, end), desc="Rows"):
            row = df.iloc[idx].to_dict()
            url = str(row.get("url", "")).strip()
            if not url or url in done_urls:
                continue

            prompt = build_prompt_for_row(row)
            caption, tags = call_model_and_extract(prompt, model=model)
            if not caption:
                caption, tags = "", ""

            tags_list = [t.strip().lower() for t in re.split(r"[,\n;]+", tags) if t.strip()]
            tags_list = tags_list[:7]
            tags_s = ", ".join(tags_list)

            row["caption"] = caption
            row["tags"] = tags_s

            pd.DataFrame([row]).to_csv(
                f_out,
                header=write_header,
                index=False
            )
            write_header = False  # Only first write should include header

            # Slight delay to avoid rate limit
            time.sleep(0.15)

    print(f"✅ Completed {end - start} rows → {output_csv}")


# -------------------------
# CLI
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate caption+tags using a GPT model for design thumbnails.")
    parser.add_argument("--input", default="data/visual_features.csv", help="Input CSV file")
    parser.add_argument("--output", default="data/ai_captions_tags.csv", help="Output CSV file (appends fields caption,tags)")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--limit", type=int, default=0, help="Limit (0 means all)")
    parser.add_argument("--model", default=API_MODEL, help="Model to use (default gpt-4o-mini)")
    args = parser.parse_args()

    process_file(args.input, args.output, start=args.start, limit=args.limit, model=args.model)
