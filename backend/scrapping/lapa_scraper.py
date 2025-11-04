import asyncio
import csv
import os
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# ---------------------- helpers ----------------------
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LAPA_OUT = DATA_DIR / "raw_lapaninja_designs.csv"
AWWW_OUT = DATA_DIR / "raw_awwwards_designs.csv"
COMBINED_OUT = DATA_DIR / "combined_designs.csv"

CSV_FIELDS = ["source", "title", "author", "price", "tags", "image", "url"]


def save_csv(rows, path: Path):
    if not rows:
        # still create an empty CSV with header for consistency
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
        print(f"Saved 0 rows -> {path}")
        return

    # de-dupe by url (and keep first occurrence)
    dedup = {}
    for r in rows:
        u = (r.get("url") or "").strip()
        if u and u not in dedup:
            dedup[u] = r
        # also allow rows without url to pass once (rare)
        if not u:
            dedup[id(r)] = r

    rows = list(dedup.values())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows -> {path}")


# ---------------------- LAPA NINJA ----------------------
async def scrape_lapaninja():
    """
    Scrape https://www.lapa.ninja/post (all pages) into the standard schema:
    source,title,author,price,tags,image,url

    Notes:
    - Paginates ?page=1..N until a page yields zero new posts.
    - Handles common lazy-image attributes (src, data-src, srcset).
    - Extracts tag chips if present.
    - 'price' is always empty for posts.
    """
    import csv
    from pathlib import Path
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    import pandas as pd

    BASE = "https://www.lapa.ninja"
    LIST = f"{BASE}/post"
    OUT_FIELDS = ["source", "title", "author", "price", "tags", "image", "url"]

    # Heuristics for post cards:
    # - parent card container often has: ".rounded-md.shadow-sm" or ".rounded-lg.shadow-sm"
    # - links to detail pages look like: a[href^="/post/"]
    # - title usually near the link inside an <h3> or div
    # - tags are chips with inline-flex classes
    CARD_SELECTORS = [
        "div.rounded-md.shadow-sm",
        "div.rounded-lg.shadow-sm",
        "div.w-s.bg-white.rounded-md",
        "article",  # fallback
    ]

    def pick_first(soup, selectors):
        for sel in selectors:
            nodes = soup.select(sel)
            if nodes:
                return nodes
        return []

    def extract_img(el):
        # Try data-src, srcset first (common for lazy loading)
        if el is None:
            return ""
        for attr in ("data-src", "data-lazy-src", "srcset", "data-srcset", "src"):
            val = el.get(attr)
            if val:
                if " " in val and "http" in val:
                    # srcset style: "url 1x, url2 2x" => take first URL
                    return val.split(",")[0].strip().split(" ")[0].strip()
                return val.strip()
        return ""

    rows = []
    seen_urls = set()

    async with async_playwright() as p:
        # Chromium tends to work best here
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1400, "height": 1000},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        )
        page = await context.new_page()

        print("Scraping Lapa Ninja Posts with pagination...")

        page_num = 1
        max_pages = 200  # safety cap
        added_any = True

        while page_num <= max_pages and added_any:
            url = f"{LIST}/page/{page_num}"
            if page_num == 1:
                url = LIST  # the first page is usually without ?page=1

            print(f"Fetching page {page_num}: {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except PlaywrightTimeoutError:
                print(f"Timeout on page {page_num}, stopping.")
                break

            # Give lazy content a moment
            try:
                await page.wait_for_timeout(1200)
                # Wait for at least one post link if possible
                try:
                    await page.wait_for_selector("a[href^='/post/']", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
            except Exception:
                pass

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Find a set of likely card containers
            cards = pick_first(soup, CARD_SELECTORS)
            if not cards:
                # If no obvious card container, fall back to anchoring off the post links
                post_links = soup.select("a[href^='/post/']")
                # De-duplicate by their parent containers
                cards = list({link.find_parent() for link in post_links if link.find_parent()})

            found_this_page = 0

            for card in cards:
                # The post link
                link_el = card.select_one("a[href^='/post/']")
                if not link_el or not link_el.get("href"):
                    continue
                href = link_el["href"].strip()
                url_full = href if href.startswith("http") else f"{BASE}{href}"

                if url_full in seen_urls:
                    continue

                # Title: try common title nodes near the link
                title_el = (
                    card.select_one("h3") or
                    card.select_one("h2") or
                    link_el
                )
                title = (title_el.get_text(strip=True) if title_el else "").strip()

                # Author: sometimes appears as a small text line; fallback to empty
                author_el = (
                    card.select_one("p.text-sm") or
                    card.select_one(".author, .byline, .text-xs, small")
                )
                author = (author_el.get_text(strip=True) if author_el else "").strip()

                # Image inside the card
                img_el = card.select_one("img")
                image = extract_img(img_el)

                # Tags (chips)
                tag_nodes = card.select("a[class*='inline-flex'], span[class*='inline-flex']")
                tags = []
                for t in tag_nodes:
                    txt = t.get_text(strip=True)
                    # Filter obvious non-tag text like the title repeating
                    if txt and txt.lower() not in (title.lower(), "read more"):
                        tags.append(txt)
                tags_str = ", ".join(sorted(set(tags))) if tags else ""

                rows.append({
                    "source": "Lapa Ninja (Post)",
                    "title": title,
                    "author": author,
                    "price": "",
                    "tags": tags_str,
                    "image": image,
                    "url": url_full,
                })
                seen_urls.add(url_full)
                found_this_page += 1

            print(f"Page {page_num} extracted {found_this_page} posts.")

            # Stop if no new posts on this page
            if found_this_page == 0:
                print("No new posts found; stopping pagination.")
                break

            page_num += 1

        await browser.close()

    # Final de-dup (by URL)
    if rows:
        dedup = {}
        for r in rows:
            u = (r.get("url") or "").strip()
            if u and u not in dedup:
                dedup[u] = r
        rows = list(dedup.values())

    # Save CSV alongside your other data files
    out_path = Path(__file__).parent / "data" / "raw_lapaninja_posts.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} Lapa posts -> {out_path}")
    return pd.DataFrame(rows, columns=OUT_FIELDS)



# ---------------------- AWWWARDS ----------------------
async def scrape_awwwards(pages=5):
    print("Starting Awwwards scraper...")
    scraped = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for page_num in range(1, pages + 1):
            url = f"https://www.awwwards.com/websites/?page={page_num}"
            print(f"Scraping Awwwards page {page_num}: {url}")

            try:
                await page.goto(url, timeout=120000, wait_until="domcontentloaded")

                # primary selector for current layout
                try:
                    await page.wait_for_selector("div.card-site", timeout=30000)
                except PlaywrightTimeoutError:
                    print("No .card-site found, trying a fallback...")
                    # A defensive fallback — less strict; if it also fails we skip page
                    await page.wait_for_selector("figure img", timeout=15000)

                # pull more lazy cards
                for _ in range(6):
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                cards = await page.query_selector_all("div.card-site")
                print(f"Found {len(cards)} cards on page {page_num}")

                for card in cards:
                    try:
                        # Title (often in rollover or info area)
                        title_el = await card.query_selector("h3, .figure-rollover__row:nth-child(2)")
                        title = (await title_el.inner_text()) if title_el else ""

                        # Author
                        author_el = await card.query_selector(".avatar-name__title, .by a")
                        author = (await author_el.inner_text()) if author_el else ""

                        # Image
                        img_el = await card.query_selector("figure img")
                        image_url = ""
                        if img_el:
                            srcset = await img_el.get_attribute("data-srcset") or await img_el.get_attribute("srcset")
                            if srcset:
                                # srcset: "url1 1x, url2 2x"
                                image_url = srcset.split(" ")[0]
                            else:
                                image_url = await img_el.get_attribute("src") or ""

                        # Page link
                        link_el = await card.query_selector("a[href*='/sites/']")
                        link = await link_el.get_attribute("href") if link_el else ""
                        if link and not link.startswith("http"):
                            link = f"https://www.awwwards.com{link}"

                        scraped.append({
                            "source": "Awwwards",
                            "title": title.strip(),
                            "author": author.strip(),
                            "price": "",
                            "tags": "",  # tags are inconsistent on listing cards
                            "image": (image_url or "").strip(),
                            "url": (link or "").strip(),
                        })
                    except Exception as e:
                        # keep going even if one card fails
                        continue

            except Exception as e:
                print(f"Timeout or navigation error on page {page_num}: {e}")
                continue

        await browser.close()

    save_csv(scraped, AWWW_OUT)
    return pd.DataFrame(scraped, columns=CSV_FIELDS)


# ---------------------- MAIN ----------------------
async def main():
    print("Starting combined scraper...")

    # Lapa Ninja
    lapa_df = await scrape_lapaninja()

    # Awwwards
    awww_df = await scrape_awwwards(pages=5)

    # Combine and de-dupe
    combined = pd.concat([lapa_df, awww_df], ignore_index=True)

    # Drop exact duplicates by URL first, then image as a secondary pass
    if "url" in combined.columns:
        combined = combined.drop_duplicates(subset=["url"])
    if "image" in combined.columns:
        combined = combined.drop_duplicates(subset=["image"])

    combined.to_csv(COMBINED_OUT, index=False)
    print(f"Combined dataset saved -> {COMBINED_OUT}")
    print(f"Total rows: {len(combined)}")


if __name__ == "__main__":
    # Avoid Windows emoji encoding issues by keeping plain text only in prints
    asyncio.run(main())
