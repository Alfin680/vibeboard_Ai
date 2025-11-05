import argparse
import os
import re
import sys
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import pandas as pd
import requests

# --------- Console safe (no emoji on Windows) ----------
def log(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "ignore").decode())

# --------- Defaults / Paths ----------
SCRIPT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_OUT = DATA_DIR / "cleaned_designs.csv"
DEFAULT_REJECTS = DATA_DIR / "rejects.csv"

CANON = ["source", "title", "author", "price", "tags", "image", "url"]

# --------- HTTP session ----------
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "Mozilla/5.0 (compatible; VibeBoardCleaner/1.0)"})


def is_http_url(u: str) -> bool:
    try:
        p = urlparse(str(u).strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map various raw schemas to canonical fields and clean text."""
    # Flexible rename map
    rename = {}
    for c in df.columns:
        lc = c.strip().lower()
        if lc in ("image", "image_url", "img", "img_url", "thumbnail", "thumb"):
            rename[c] = "image"
        elif lc in ("url", "page_url", "site_url", "link", "external_link"):
            rename[c] = "url"
        elif lc == "tag":
            rename[c] = "tags"
        elif lc in CANON:
            rename[c] = lc

    df = df.rename(columns=rename)

    # Ensure all columns exist
    for c in CANON:
        if c not in df.columns:
            df[c] = ""

    # Keep only our canonical columns
    df = df[CANON].copy()

    # Strip whitespace / collapse spaces
    for c in ["source", "title", "author", "price", "tags", "image", "url"]:
        df[c] = (
            df[c]
            .astype(str)
            .fillna("")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    # Normalize tags -> lowercased, unique, comma-separated
    df["tags"] = df["tags"].apply(
        lambda x: ", ".join(sorted({t.strip().lower() for t in str(x).split(",") if t.strip()}))
    )

    return df


def quick_reject_reason(row) -> str:
    """Basic local checks to build a reject reason (without network)."""
    if not row["image"]:
        return "missing_image"
    if not row["url"]:
        return "missing_url"
    if not is_http_url(row["image"]):
        return "bad_image_url"
    if not is_http_url(row["url"]):
        return "bad_page_url"
    if not row["title"] and "promoted" in row["tags"].lower():
        return "promoted_no_title"
    return ""


def head_ok_image(url: str, min_bytes: int = 12000, timeout: int = 8) -> (bool, str):
    """HEAD/GET check for image validity and size (optional step)."""
    try:
        r = HTTP.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code != 200 or "image" not in r.headers.get("Content-Type", "").lower():
            # fallback GET (stream) for CDNs that don't respond well to HEAD
            r = HTTP.get(url, timeout=timeout, stream=True)
            if r.status_code != 200 or "image" not in r.headers.get("Content-Type", "").lower():
                return False, f"bad_status_or_type:{r.status_code}"
        clen = r.headers.get("Content-Length")
        if clen and clen.isdigit() and int(clen) < min_bytes:
            return False, f"too_small:{clen}"
        return True, ""
    except requests.RequestException as e:
        return False, f"request_error:{type(e).__name__}"


def load_many_csv(paths) -> pd.DataFrame:
    frames = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            log(f"Warning: file not found -> {p}")
            continue
        try:
            df = pd.read_csv(p)
            frames.append(df)
            log(f"Loaded {len(df)} rows from {p}")
        except Exception as e:
            log(f"Failed to read {p}: {e}")
    if not frames:
        return pd.DataFrame(columns=CANON)
    return pd.concat(frames, ignore_index=True)


def clean_dataframe(df: pd.DataFrame, check_images: bool = False, max_workers: int = 16) -> (pd.DataFrame, pd.DataFrame):
    """Returns (clean_df, rejects_df)."""
    if df.empty:
        return df, pd.DataFrame(columns=CANON + ["reject_reason"])

    # Normalize
    df = normalize_columns(df)

    # Basic rejects table (pre-network)
    base_rejects = []
    keep_mask = []
    for _, row in df.iterrows():
        reason = quick_reject_reason(row)
        if reason:
            base_rejects.append({**row.to_dict(), "reject_reason": reason})
            keep_mask.append(False)
        else:
            keep_mask.append(True)

    df = df[keep_mask].reset_index(drop=True)

    # De-dupe by URL, then by image
    before = len(df)
    df = df.drop_duplicates(subset=["url"])
    df = df.drop_duplicates(subset=["image"])
    log(f"Deduped {before - len(df)} rows; remaining: {len(df)}")

    # Optional network image validation
    net_rejects = []
    if check_images and not df.empty:
        log("Validating image URLs with HEAD/GET (this may take a while)...")
        futures = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for idx, row in df.iterrows():
                futures[ex.submit(head_ok_image, row["image"])] = (idx, row)
            good_indices = []
            for fut in as_completed(futures):
                idx, row = futures[fut]
                ok, why = fut.result()
                if ok:
                    good_indices.append(idx)
                else:
                    net_rejects.append({**row.to_dict(), "reject_reason": f"image_check:{why}"})
        df = df.loc[good_indices].reset_index(drop=True)

    # Final cleanups
    # Strip very short titles unless source is clearly a gallery (tune as needed)
    # (Commented out by default)
    # df = df[(df["title"].str.len() >= 2) | (df["source"].str.contains("Awwwards|Lapa", case=False))]

    rejects_df = pd.DataFrame(base_rejects + net_rejects)
    if not rejects_df.empty:
        rejects_df = rejects_df.drop_duplicates(subset=["url", "image", "reject_reason"])

    return df, rejects_df


def main():
    parser = argparse.ArgumentParser(description="Clean combined design datasets (Lapa + Awwwards).")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            # str(DATA_DIR / "raw_lapaninja_designs.csv"),
            # str(DATA_DIR / "raw_lapaninja_posts.csv"),
            # str(DATA_DIR / "raw_awwwards_designs.csv"),
            str(DATA_DIR / "combined_designs.csv"),
        ],
        help="One or more CSV paths to merge and clean."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUT), help="Path for cleaned CSV.")
    parser.add_argument("--rejects", default=str(DEFAULT_REJECTS), help="Path for rejects CSV.")
    parser.add_argument("--check-images", action="store_true", help="Validate image URLs via HEAD/GET.")
    parser.add_argument("--min-bytes", type=int, default=12000, help="Minimum Content-Length for image check.")
    parser.add_argument("--workers", type=int, default=16, help="Max workers for image validation.")
    args = parser.parse_args()

    log("Loading input CSVs...")
    raw_df = load_many_csv(args.inputs)
    if raw_df.empty:
        log("No input data found. Exiting.")
        sys.exit(0)

    log(f"Total loaded rows: {len(raw_df)}")
    clean_df, rejects_df = clean_dataframe(raw_df, check_images=args.check_images, max_workers=args.workers)

    out_path = Path(args.output)
    rej_path = Path(args.rejects)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save cleaned
    clean_df.to_csv(out_path, index=False)
    log(f"Cleaned dataset saved -> {out_path}")
    log(f"Final cleaned rows: {len(clean_df)}")

    # Save rejects with reasons
    if not rejects_df.empty:
        rejects_df.to_csv(rej_path, index=False)
        log(f"Rejects saved -> {rej_path} ({len(rejects_df)} rows)")
    else:
        log("No rejects recorded (beyond dedup).")


if __name__ == "__main__":
    main()
