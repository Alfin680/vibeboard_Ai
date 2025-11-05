# # backend/scrapping/extract_features.py
# import os
# import io
# import json
# import argparse
# from pathlib import Path
# from typing import List, Tuple, Dict, Any
# import hashlib

# import numpy as np
# import pandas as pd
# from PIL import Image
# from sklearn.cluster import KMeans
# import colorsys
# import torch
# from transformers import CLIPProcessor, CLIPModel
# from tqdm import tqdm
# import requests

# # Optional: perceptual merging if installed
# try:
#     from colormath.color_objects import sRGBColor, LabColor
#     from colormath.color_conversions import convert_color
#     from colormath.color_diff import delta_e_cie2000
#     HAVE_COLORMATH = True
# except Exception:
#     HAVE_COLORMATH = False

# # -------------------------
# # CONFIG
# # -------------------------
# MODEL_NAME = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# K = 5
# SAMPLE_PIXELS = 4000
# MIN_AREA_FRAC = 0.08
# TOP_N_COLORS = 2
# PRIMARY_WEIGHT_THRESHOLD = 0.18
# MERGE_SIMILAR_DELTA_E = 6.0

# ELEMENT_THRESHOLD = 0.15
# MOOD_THRESHOLD = 0.12
# COLOR_FAMILY_THRESHOLD = 0.12

# UI_ELEMENTS = [
#     "hero image", "hero illustration", "rounded buttons", "cta button", "card list",
#     "grid layout", "sidebar", "top navigation", "large typography", "form", "testimonial",
#     "pricing cards", "feature list", "logo", "footer", "search bar", "data table",
#     "chart", "avatar", "icon list", "illustration", "centered hero", "split screen",
#     "two-column layout", "single column", "carousel", "video background"
# ]

# MOODS = [
#     "minimal", "playful", "calm", "bold", "elegant", "professional",
#     "vibrant", "warm", "cool", "trustworthy", "creative", "luxury", "retro",
#     "modern", "futuristic", "artistic", "friendly", "serious", "moody"
# ]

# COLOR_FAMILIES = [
#     "red", "orange", "yellow", "green", "teal", "blue",
#     "purple", "magenta", "pink", "brown", "gray", "black", "white"
# ]

# HEADERS = {"User-Agent": "VibeBoardBot/1.0 (+design discovery)"}

# # -------------------------
# # Utilities
# # -------------------------
# def rgb_to_hex(rgb: List[int]) -> str:
#     r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
#     return "#{:02x}{:02x}{:02x}".format(r, g, b)

# def hex_to_descriptor(hex_color: str) -> str:
#     if not hex_color:
#         return ""
#     hex_color = hex_color.lstrip('#')
#     r = int(hex_color[0:2], 16)
#     g = int(hex_color[2:4], 16)
#     b = int(hex_color[4:6], 16)
#     h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
#     hue_deg = h * 360
#     if s < 0.12:
#         fam = "neutral"
#     elif hue_deg < 20 or hue_deg >= 340:
#         fam = "red"
#     elif hue_deg < 50:
#         fam = "orange"
#     elif hue_deg < 80:
#         fam = "yellow"
#     elif hue_deg < 160:
#         fam = "green"
#     elif hue_deg < 200:
#         fam = "teal"
#     elif hue_deg < 260:
#         fam = "blue"
#     elif hue_deg < 300:
#         fam = "purple"
#     else:
#         fam = "magenta"
#     tone = "muted" if s < 0.35 else "bright"
#     if l < 0.25:
#         tone = "dark " + tone
#     elif l > 0.85:
#         tone = "light " + tone
#     return f"{tone} {fam}".strip()

# def is_near_white_rgb(rgb: List[int]) -> bool:
#     r, g, b = rgb
#     return (r > 240 and g > 240 and b > 240) or (np.mean(rgb) > 245)

# def url_to_cache_path(url: str, cache_dir: Path) -> Path:
#     h = hashlib.md5(url.encode("utf-8")).hexdigest()
#     ext = ".jpg"
#     # try to preserve extension if present
#     for e in [".jpg", ".jpeg", ".png", ".webp"]:
#         if url.lower().endswith(e):
#             ext = e
#             break
#     return cache_dir / f"{h}{ext}"

# def fetch_image(url: str, cache_dir: Path) -> Image.Image:
#     cache_dir.mkdir(parents=True, exist_ok=True)
#     path = url_to_cache_path(url, cache_dir)
#     if path.exists():
#         return Image.open(path).convert("RGB")
#     r = requests.get(url, headers=HEADERS, timeout=15)
#     r.raise_for_status()
#     img = Image.open(io.BytesIO(r.content)).convert("RGB")
#     # persist
#     try:
#         img.save(path)
#     except Exception:
#         pass
#     return img

# # -------------------------
# # Color extraction (area-based)
# # -------------------------
# def compute_dominant_colors_area_based(
#     pil_img: Image.Image,
#     k: int = K,
#     sample_pixels: int = SAMPLE_PIXELS,
#     top_n: int = TOP_N_COLORS,
#     min_area_frac: float = MIN_AREA_FRAC,
#     primary_weight_threshold: float = PRIMARY_WEIGHT_THRESHOLD,
#     merge_similar_delta_e: float = MERGE_SIMILAR_DELTA_E
# ) -> Tuple[List[str], Dict[str, float], str]:

#     img_arr = np.array(pil_img.convert("RGB"))
#     H, W, _ = img_arr.shape
#     total_pixels = H * W
#     flat = img_arr.reshape(-1, 3)
#     n = len(flat)
#     if n == 0:
#         return [], {}, ""

#     if n > sample_pixels:
#         idx = np.random.choice(n, sample_pixels, replace=False)
#         sample = flat[idx]
#     else:
#         sample = flat

#     k_used = min(k, max(2, int(len(sample) / 50)))
#     # n_init default change in sklearn 1.4; set explicitly for stability
#     kmeans = KMeans(n_clusters=k_used, random_state=42, n_init=5).fit(sample)
#     centers = kmeans.cluster_centers_.astype(int)

#     full = flat.astype(np.float32)
#     dists = np.linalg.norm(full[:, None, :] - centers[None, :, :], axis=2)
#     labels_full = np.argmin(dists, axis=1)
#     unique, counts = np.unique(labels_full, return_counts=True)
#     label_to_count = {int(u): int(c) for u, c in zip(unique, counts)}

#     clusters = []
#     for idx_center, center_rgb in enumerate(centers):
#         cnt = label_to_count.get(idx_center, 0)
#         weight = cnt / total_pixels
#         clusters.append({"rgb": center_rgb.tolist(), "weight": weight})

#     # optional perceptual merge
#     merged = []
#     if HAVE_COLORMATH:
#         used = set()
#         for i, base in enumerate(clusters):
#             if i in used:
#                 continue
#             base_rgb = base["rgb"]
#             base_lab = convert_color(sRGBColor(*[v/255.0 for v in base_rgb]), LabColor)
#             total_weight = base["weight"]
#             accum_rgb = np.array(base_rgb) * base["weight"]
#             used.add(i)
#             for j in range(i+1, len(clusters)):
#                 if j in used:
#                     continue
#                 comp_rgb = clusters[j]["rgb"]
#                 comp_lab = convert_color(sRGBColor(*[v/255.0 for v in comp_rgb]), LabColor)
#                 dE = delta_e_cie2000(base_lab, comp_lab)
#                 if dE <= MERGE_SIMILAR_DELTA_E:
#                     accum_rgb += np.array(comp_rgb) * clusters[j]["weight"]
#                     total_weight += clusters[j]["weight"]
#                     used.add(j)
#             avg_rgb = (accum_rgb / max(total_weight, 1e-8)).round().astype(int).tolist()
#             merged.append({"rgb": avg_rgb, "weight": total_weight})
#     else:
#         merged = clusters

#     merged_sorted = sorted(merged, key=lambda x: -x["weight"])
#     filtered = [c for c in merged_sorted if c["weight"] >= min_area_frac] or merged_sorted[:max(1, top_n)]

#     selected = filtered[:top_n]
#     if len(selected) >= 1 and is_near_white_rgb(selected[0]["rgb"]):
#         non_white = None
#         for c in merged_sorted:
#             if not is_near_white_rgb(c["rgb"]):
#                 non_white = c
#                 break
#         if non_white and non_white["weight"] >= primary_weight_threshold:
#             secondary_keep = selected[0] if selected[0]["weight"] >= min_area_frac else None
#             new_selected = [non_white]
#             if secondary_keep:
#                 new_selected.append(secondary_keep)
#             selected = new_selected[:top_n]

#     top_colors = [rgb_to_hex(c["rgb"]) for c in selected]
#     weights = {rgb_to_hex(c["rgb"]): round(float(c["weight"]), 4) for c in selected}
#     primary_hex = top_colors[0] if top_colors else ""
#     primary_descriptor = hex_to_descriptor(primary_hex) if primary_hex else ""

#     return top_colors, weights, primary_descriptor

# # -------------------------
# # CLIP zero-shot
# # -------------------------
# class ClipZeroShot:
#     def __init__(self, model_name: str = MODEL_NAME, device: str = DEVICE):
#         self.device = device
#         self.model = CLIPModel.from_pretrained(model_name).to(self.device)
#         self.processor = CLIPProcessor.from_pretrained(model_name)
#         self.model.eval()

#     def image_embedding(self, pil_image: Image.Image) -> np.ndarray:
#         inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)
#         with torch.no_grad():
#             img_feats = self.model.get_image_features(**inputs)
#         img_feats = img_feats / img_feats.norm(p=2, dim=-1, keepdim=True)
#         return img_feats.cpu().numpy()[0]

#     def text_embeddings(self, texts: List[str]) -> np.ndarray:
#         inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(self.device)
#         with torch.no_grad():
#             txt_feats = self.model.get_text_features(**inputs)
#         txt_feats = txt_feats / txt_feats.norm(p=2, dim=-1, keepdim=True)
#         return txt_feats.cpu().numpy()

#     def zero_shot(self, pil_image: Image.Image, candidate_texts: List[str]) -> List[float]:
#         img_emb = self.image_embedding(pil_image)
#         txt_embs = self.text_embeddings(candidate_texts)
#         sims_all = (txt_embs @ img_emb).reshape(-1)
#         return sims_all.tolist()

# # -------------------------
# # Combined extractor
# # -------------------------
# def extract_visual_hints_with_clip(
#     pil: Image.Image,
#     ui_elements: List[str] = UI_ELEMENTS,
#     moods: List[str] = MOODS,
#     color_families: List[str] = COLOR_FAMILIES,
#     clip_model: ClipZeroShot = None
# ) -> Dict[str, Any]:

#     top_colors, weights, primary_descriptor = compute_dominant_colors_area_based(
#         pil,
#         k=K,
#         sample_pixels=SAMPLE_PIXELS,
#         top_n=TOP_N_COLORS,
#         min_area_frac=MIN_AREA_FRAC,
#         primary_weight_threshold=PRIMARY_WEIGHT_THRESHOLD
#     )

#     if clip_model is None:
#         clip_model = ClipZeroShot()

#     elem_sims = clip_model.zero_shot(pil, ui_elements)
#     elem_pairs = sorted([(ui_elements[i], float(elem_sims[i])) for i in range(len(ui_elements))],
#                         key=lambda x: -x[1])

#     mood_sims = clip_model.zero_shot(pil, moods)
#     mood_pairs = sorted([(moods[i], float(mood_sims[i])) for i in range(len(moods))],
#                         key=lambda x: -x[1])

#     color_sims = clip_model.zero_shot(pil, color_families)
#     color_pairs = sorted([(color_families[i], float(color_sims[i])) for i in range(len(color_families))],
#                          key=lambda x: -x[1])

#     elements_present = [p for p, s in elem_pairs if s >= ELEMENT_THRESHOLD][:6]
#     mood_present = [p for p, s in mood_pairs if s >= MOOD_THRESHOLD][:3]
#     color_family_scores = {p: round(s, 4) for p, s in color_pairs}

#     primary_hex = top_colors[0] if top_colors else ""
#     primary_weight = weights.get(primary_hex, 0.0) if primary_hex else 0.0
#     fam_guess = primary_descriptor.split()[-1] if primary_descriptor else ""
#     fam_score = color_family_scores.get(fam_guess, 0.0) if fam_guess else 0.0
#     elem_support = float(elem_pairs[0][1]) if elem_pairs else 0.0

#     conf = 0.5
#     conf += min(0.25, primary_weight * 0.5)
#     conf += min(0.2, elem_support * 0.3)
#     conf += min(0.15, fam_score * 0.2)
#     conf = max(0.0, min(1.0, round(conf, 2)))

#     return {
#         "dominant_colors": top_colors,
#         "color_weights": weights,
#         "primary_hex": primary_hex,
#         "primary_descriptor": primary_descriptor,
#         "elements": elements_present,
#         "mood_keywords": mood_present,
#         "color_family_scores": color_family_scores,
#         "confidence": conf,
#         "raw_element_scores": dict(elem_pairs[:10]),
#         "raw_mood_scores": dict(mood_pairs[:10]),
#         "raw_color_family_scores": dict(color_pairs[:10]),
#     }

# # -------------------------
# # Batch driver
# # -------------------------
# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--input", default="data/cleaned_designs.csv",
#                     help="CSV with columns: url,image,title,... (image is a URL)")
#     ap.add_argument("--out", default="data/visual_features.csv")
#     ap.add_argument("--cache", default="data/thumb_cache")
#     ap.add_argument("--resume", action="store_true", help="skip rows already present in --out")
#     ap.add_argument("--limit", type=int, default=0)
#     args = ap.parse_args()

#     inp = Path(args.input)
#     outp = Path(args.out)
#     cache_dir = Path(args.cache)
#     outp.parent.mkdir(parents=True, exist_ok=True)
#     cache_dir.mkdir(parents=True, exist_ok=True)

#     df = pd.read_csv(inp)
#     if args.limit > 0:
#         df = df.head(args.limit)

#     # prepare resume
#     done_urls = set()
#     rows_out = []
#     if args.resume and outp.exists():
#         prev = pd.read_csv(outp)
#         if "url" in prev.columns:
#             done_urls = set(prev["url"].astype(str))
#             rows_out = prev.to_dict(orient="records")

#     clip = ClipZeroShot(MODEL_NAME, DEVICE)

#     for _, row in tqdm(df.iterrows(), total=len(df)):
#         url = str(row.get("url", "")).strip()
#         img_url = str(row.get("image", "")).strip()
#         if not url or not img_url:
#             continue
#         if args.resume and url in done_urls:
#             continue

#         try:
#             pil = fetch_image(img_url, cache_dir=cache_dir)
#         except Exception as e:
#             # skip bad images
#             continue

#         try:
#             feats = extract_visual_hints_with_clip(pil, clip_model=clip)
#         except Exception:
#             continue

#         rows_out.append({
#             "source": row.get("source",""),
#             "title": row.get("title",""),
#             "url": url,
#             "image": img_url,
#             "dominant_colors": json.dumps(feats["dominant_colors"]),
#             "color_weights": json.dumps(feats["color_weights"]),
#             "primary_hex": feats["primary_hex"],
#             "primary_descriptor": feats["primary_descriptor"],
#             "elements": ", ".join(feats["elements"]),
#             "mood_keywords": ", ".join(feats["mood_keywords"]),
#             "confidence": feats["confidence"]
#         })

#         if len(rows_out) % 200 == 0:
#             pd.DataFrame(rows_out).to_csv(outp, index=False)

#     pd.DataFrame(rows_out).to_csv(outp, index=False)
#     print(f"wrote {len(rows_out)} rows -> {outp}")

# if __name__ == "__main__":
#     main()

import os
import io
import json
import argparse
import hashlib
import colorsys
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np

# --- Compatibility patch for NumPy >=1.24 (fixes module 'numpy' has no attribute 'asscalar') ---
if not hasattr(np, "asscalar"):
    def _asscalar(x):
        try:
            return x.item()
        except Exception:
            arr = np.asarray(x)
            if arr.size == 1:
                return arr.reshape(()).tolist()
            raise
    np.asscalar = _asscalar

import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans
import torch
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm
import requests

# Optional: perceptual merging (if installed)
try:
    from colormath.color_objects import sRGBColor, LabColor
    from colormath.color_conversions import convert_color
    from colormath.color_diff import delta_e_cie2000
    HAVE_COLORMATH = True
except Exception:
    HAVE_COLORMATH = False


# -------------------------
# CONFIG
# -------------------------
MODEL_NAME = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

K = 5
SAMPLE_PIXELS = 4000
MIN_AREA_FRAC = 0.05
TOP_N_COLORS = 2
PRIMARY_WEIGHT_THRESHOLD = 0.18
MERGE_SIMILAR_DELTA_E = 6.0

ELEMENT_THRESHOLD = 0.15
MOOD_THRESHOLD = 0.12
COLOR_FAMILY_THRESHOLD = 0.12

UI_ELEMENTS = [
    "hero image", "hero illustration", "rounded buttons", "cta button", "card list",
    "grid layout", "sidebar", "top navigation", "large typography", "form", "testimonial",
    "pricing cards", "feature list", "logo", "footer", "search bar", "data table",
    "chart", "avatar", "icon list", "illustration", "centered hero", "split screen",
    "two-column layout", "single column", "carousel", "video background"
]

MOODS = [
    "minimal", "playful", "calm", "bold", "elegant", "professional",
    "vibrant", "warm", "cool", "trustworthy", "creative", "luxury", "retro",
    "modern", "futuristic", "artistic", "friendly", "serious", "moody"
]

COLOR_FAMILIES = [
    "red", "orange", "yellow", "green", "teal", "blue",
    "purple", "magenta", "pink", "brown", "gray", "black", "white"
]

HEADERS = {"User-Agent": "VibeBoardBot/1.0 (+design discovery)"}


# -------------------------
# UTILITIES
# -------------------------
def rgb_to_hex(rgb: List[int]) -> str:
    """Ensure RGB is 6-digit hex and clamped to [0,255]."""
    if rgb is None or len(rgb) < 3:
        return ""
    r, g, b = [max(0, min(255, int(round(v)))) for v in rgb]
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def hex_to_descriptor(hex_color: str) -> str:
    """Converts hex color to a human-readable descriptor."""
    if not hex_color:
        return ""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        hex_color = hex_color.zfill(6)

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = h * 360

    mean = (r + g + b) / 3.0
    if mean <= 20:
        return "dark neutral"
    if mean >= 235:
        return "light neutral"

    if s < 0.10:
        tone = "light" if l > 0.7 else ("dark" if l < 0.3 else "muted")
        return f"{tone} gray".strip()

    if hue_deg < 15 or hue_deg >= 345:
        fam = "red"
    elif hue_deg < 45:
        fam = "orange"
    elif hue_deg < 70:
        fam = "yellow"
    elif hue_deg < 160:
        fam = "green"
    elif hue_deg < 200:
        fam = "teal"
    elif hue_deg < 260:
        fam = "blue"
    elif hue_deg < 300:
        fam = "purple"
    elif hue_deg < 330:
        fam = "magenta"
    else:
        fam = "red"

    tone = "muted" if s < 0.35 else "bright"
    if l < 0.25:
        tone = "dark " + tone
    elif l > 0.85:
        tone = "light " + tone

    return f"{tone} {fam}".strip()


def is_near_white_rgb(rgb: List[int]) -> bool:
    r, g, b = rgb
    return (r > 240 and g > 240 and b > 240) or (np.mean(rgb) > 245)


def url_to_cache_path(url: str, cache_dir: Path) -> Path:
    h = hashlib.md5(url.encode("utf-8")).hexdigest()
    ext = ".jpg"
    for e in [".jpg", ".jpeg", ".png", ".webp"]:
        if url.lower().endswith(e):
            ext = e
            break
    return cache_dir / f"{h}{ext}"


def fetch_image(url: str, cache_dir: Path) -> Image.Image:
    """Downloads and caches image."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = url_to_cache_path(url, cache_dir)
    if path.exists():
        return Image.open(path).convert("RGB")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        img.save(path)
        return img
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")


# -------------------------
# COLOR EXTRACTION
# -------------------------
def compute_dominant_colors_area_based(
    pil_img: Image.Image,
    k: int = K,
    sample_pixels: int = SAMPLE_PIXELS,
    top_n: int = TOP_N_COLORS,
    min_area_frac: float = MIN_AREA_FRAC,
    primary_weight_threshold: float = PRIMARY_WEIGHT_THRESHOLD,
    merge_similar_delta_e: float = MERGE_SIMILAR_DELTA_E
) -> Tuple[List[str], Dict[str, float], str]:

    img_arr = np.array(pil_img.convert("RGB"))
    H, W, _ = img_arr.shape
    total_pixels = H * W
    flat = img_arr.reshape(-1, 3)

    if len(flat) == 0:
        return [], {}, ""

    if len(flat) > sample_pixels:
        idx = np.random.choice(len(flat), sample_pixels, replace=False)
        sample = flat[idx]
    else:
        sample = flat

    k_used = min(k, max(2, int(len(sample) / 50)))
    kmeans = KMeans(n_clusters=k_used, random_state=42, n_init=5).fit(sample)
    centers = np.clip(np.round(kmeans.cluster_centers_), 0, 255).astype(int)

    dists = np.linalg.norm(flat[:, None, :] - centers[None, :, :], axis=2)
    labels_full = np.argmin(dists, axis=1)
    unique, counts = np.unique(labels_full, return_counts=True)
    label_to_count = {int(u): int(c) for u, c in zip(unique, counts)}

    clusters = []
    for idx_center, center_rgb in enumerate(centers):
        cnt = label_to_count.get(idx_center, 0)
        weight = cnt / total_pixels
        clusters.append({"rgb": center_rgb.tolist(), "weight": weight})

    merged = clusters
    if HAVE_COLORMATH:
        used = set()
        merged = []
        for i, base in enumerate(clusters):
            if i in used:
                continue
            base_rgb = base["rgb"]
            base_lab = convert_color(sRGBColor(*[v / 255.0 for v in base_rgb]), LabColor)
            total_weight = base["weight"]
            accum_rgb = np.array(base_rgb) * base["weight"]
            used.add(i)
            for j in range(i + 1, len(clusters)):
                if j in used:
                    continue
                comp_rgb = clusters[j]["rgb"]
                comp_lab = convert_color(sRGBColor(*[v / 255.0 for v in comp_rgb]), LabColor)
                dE = delta_e_cie2000(base_lab, comp_lab)
                if dE <= merge_similar_delta_e:
                    accum_rgb += np.array(comp_rgb) * clusters[j]["weight"]
                    total_weight += clusters[j]["weight"]
                    used.add(j)
            avg_rgb = (accum_rgb / max(total_weight, 1e-8)).round().astype(int).tolist()
            merged.append({"rgb": avg_rgb, "weight": total_weight})

    merged_sorted = sorted(merged, key=lambda x: -x["weight"])
    filtered = [c for c in merged_sorted if c["weight"] >= min_area_frac] or merged_sorted[:max(1, top_n)]

    selected = filtered[:top_n]
    if len(selected) >= 1 and is_near_white_rgb(selected[0]["rgb"]):
        non_white = None
        for c in merged_sorted:
            if not is_near_white_rgb(c["rgb"]):
                non_white = c
                break
        if non_white and non_white["weight"] >= primary_weight_threshold:
            selected = [non_white] + selected[:1]

    top_colors = [rgb_to_hex(c["rgb"]) for c in selected]
    weights = {rgb_to_hex(c["rgb"]): round(float(c["weight"]), 4) for c in selected}
    primary_hex = top_colors[0] if top_colors else ""
    primary_descriptor = hex_to_descriptor(primary_hex) if primary_hex else ""
    return top_colors, weights, primary_descriptor


# -------------------------
# CLIP ZERO-SHOT
# -------------------------
class ClipZeroShot:
    def __init__(self, model_name: str = MODEL_NAME, device: str = DEVICE):
        self.device = device
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def image_embedding(self, pil_image: Image.Image) -> np.ndarray:
        inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            img_feats = self.model.get_image_features(**inputs)
        img_feats = img_feats / img_feats.norm(p=2, dim=-1, keepdim=True)
        return img_feats.cpu().numpy()[0]

    def text_embeddings(self, texts: List[str]) -> np.ndarray:
        inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            txt_feats = self.model.get_text_features(**inputs)
        txt_feats = txt_feats / txt_feats.norm(p=2, dim=-1, keepdim=True)
        return txt_feats.cpu().numpy()

    def zero_shot(self, pil_image: Image.Image, candidate_texts: List[str]) -> List[float]:
        img_emb = self.image_embedding(pil_image)
        txt_embs = self.text_embeddings(candidate_texts)
        sims_all = (txt_embs @ img_emb).reshape(-1)
        return sims_all.tolist()


# -------------------------
# FEATURE EXTRACTION
# -------------------------
def extract_visual_hints_with_clip(pil: Image.Image, clip_model: ClipZeroShot = None) -> Dict[str, Any]:
    top_colors, weights, primary_descriptor = compute_dominant_colors_area_based(pil)
    if clip_model is None:
        clip_model = ClipZeroShot()

    elem_sims = clip_model.zero_shot(pil, UI_ELEMENTS)
    mood_sims = clip_model.zero_shot(pil, MOODS)
    color_sims = clip_model.zero_shot(pil, COLOR_FAMILIES)

    elem_pairs = sorted(zip(UI_ELEMENTS, elem_sims), key=lambda x: -x[1])
    mood_pairs = sorted(zip(MOODS, mood_sims), key=lambda x: -x[1])
    color_pairs = sorted(zip(COLOR_FAMILIES, color_sims), key=lambda x: -x[1])

    elements_present = [p for p, s in elem_pairs if s >= ELEMENT_THRESHOLD][:6]
    mood_present = [p for p, s in mood_pairs if s >= MOOD_THRESHOLD][:3]
    color_family_scores = {p: round(s, 4) for p, s in color_pairs}

    primary_hex = top_colors[0] if top_colors else ""
    conf = round(0.5 + min(0.25, weights.get(primary_hex, 0) * 0.5), 2)

    return {
        "dominant_colors": top_colors,
        "color_weights": weights,
        "primary_hex": primary_hex,
        "primary_descriptor": primary_descriptor,
        "elements": elements_present,
        "mood_keywords": mood_present,
        "color_family_scores": color_family_scores,
        "confidence": conf
    }


# -------------------------
# MAIN PIPELINE
# -------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/cleaned_designs.csv")
    ap.add_argument("--out", default="data/visual_features.csv")
    ap.add_argument("--cache", default="data/thumb_cache")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if args.limit > 0:
        df = df.head(args.limit)

    outp = Path(args.out)
    cache_dir = Path(args.cache)
    outp.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    clip = ClipZeroShot(MODEL_NAME, DEVICE)
    rows_out = []

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        url = str(row.get("url", "")).strip()
        img_url = str(row.get("image", "")).strip()
        if not url or not img_url:
            print(f"Skipping row {idx}: missing url or image")
            continue

        try:
            pil = fetch_image(img_url, cache_dir=cache_dir)
            feats = extract_visual_hints_with_clip(pil, clip_model=clip)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue

        rows_out.append({
            "source": row.get("source", ""),
            "title": row.get("title", ""),
            "url": url,
            "image": img_url,
            "dominant_colors": json.dumps(feats["dominant_colors"]),
            "color_weights": json.dumps(feats["color_weights"]),
            "primary_hex": feats["primary_hex"],
            "primary_descriptor": feats["primary_descriptor"],
            "elements": ", ".join(feats["elements"]),
            "mood_keywords": ", ".join(feats["mood_keywords"]),
            "confidence": feats["confidence"]
        })

        if len(rows_out) % 50 == 0:
            pd.DataFrame(rows_out).to_csv(outp, index=False)

    pd.DataFrame(rows_out).to_csv(outp, index=False)
    print(f"Wrote {len(rows_out)} rows -> {outp}")


if __name__ == "__main__":
    main()
