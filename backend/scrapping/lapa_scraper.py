import asyncio
import csv
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# =========================
# LAPA NINJA SCRAPER
# =========================
async def scrape_lapaninja():
    url = "https://www.lapa.ninja/templates/"
    scraped = []

    print(f"🌐 Opening {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector("div.bg-white.rounded-lg", timeout=20000)
        except PlaywrightTimeoutError:
            print("⚠ Timeout waiting for Lapa Ninja cards. Continuing...")

        print("🔄 Scrolling to load all templates...")

        previous_height = 0
        same_height_count = 0
        while True:
            height = await page.evaluate("document.body.scrollHeight")
            if height == previous_height:
                same_height_count += 1
                if same_height_count >= 3:
                    break
            else:
                same_height_count = 0
                previous_height = height

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

        print("✅ Reached end of Lapa Ninja page.")
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.bg-white.rounded-lg.shadow-sm.border")

    print(f"✅ Found {len(cards)} cards on Lapa Ninja.")

    for card in cards:
        title = card.select_one("h3.font-semibold")
        author = card.select_one("p.text-sm")
        price = card.select_one("span.text-lg.font-bold")
        img = card.select_one("img")
        tags = [t.get_text(strip=True) for t in card.select("a[class*='inline-flex']")]
        link = card.select_one("a[href*='/templates/']")

        scraped.append({
            "source": "Lapa Ninja",
            "title": title.get_text(strip=True) if title else "",
            "author": author.get_text(strip=True) if author else "",
            "price": price.get_text(strip=True) if price else "",
            "tags": ", ".join(tags) if tags else "",
            "image": img["src"].strip() if img and img.has_attr("src") else "",
            "url": (
                f"https://www.lapa.ninja{link['href'].strip()}"
                if link and link.has_attr("href") and link['href'].startswith("/")
                else (link['href'].strip() if link and link.has_attr("href") else "")
            ),
        })

    file_path = Path("data/raw_lapaninja_designs.csv")
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=scraped[0].keys())
        writer.writeheader()
        writer.writerows(scraped)

    print(f"💾 Saved {len(scraped)} Lapa Ninja templates → {file_path}")
    return pd.DataFrame(scraped)


# =========================
# AWWWARDS SCRAPER
# =========================
async def scrape_awwwards(pages=5):
    print("🌍 Starting Awwwards scraper...")
    scraped = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for page_num in range(1, pages + 1):
            url = f"https://www.awwwards.com/websites/?page={page_num}"
            print(f"🌍 Scraping Awwwards page {page_num}: {url}")

            try:
                await page.goto(url, timeout=120000)
                
                # Wait for any card to appear
                try:
                    await page.wait_for_selector("div.card-site", timeout=30000)
                except PlaywrightTimeoutError:
                    print("⚠ No .card-site found, trying fallback selector...")
                    await page.wait_for_selector("a[data-v-clipboard-text]", timeout=15000)

                # Scroll to ensure all lazy cards load
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                cards = await page.query_selector_all("div.card-site")

                print(f"✅ Found {len(cards)} cards on page {page_num}")

                for card in cards:
                    try:
                        # Extract title
                        title_el = await card.query_selector("h3, .figure-rollover__row:nth-child(2)")
                        title = (await title_el.inner_text()) if title_el else ""

                        # Author
                        author_el = await card.query_selector(".avatar-name__title, .by a")
                        author = (await author_el.inner_text()) if author_el else ""

                        # Image
                        img_el = await card.query_selector("figure img")
                        img_url = None
                        if img_el:
                            srcset = await img_el.get_attribute("data-srcset") or await img_el.get_attribute("srcset")
                            img_url = srcset.split(" ")[0] if srcset else (await img_el.get_attribute("src"))

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
                            "tags": "",
                            "image": img_url or "",
                            "url": link or "",
                        })
                    except Exception as e:
                        print("⚠ Error parsing a card:", e)
                        continue

            except Exception as e:
                print(f"⚠ Timeout or error on page {page_num}: {e}")
                continue

        await browser.close()

    # Save
    file_path = Path("data/raw_awwwards_designs.csv")
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(scraped)
    df.to_csv(file_path, index=False)
    print(f"💾 Saved {len(scraped)} Awwwards templates → {file_path}")
    return df



# =========================
# MAIN COMBINED FUNCTION
# =========================
async def main():
    print("🚀 Starting combined scraper...")

    lapa_data = await scrape_lapaninja()
    aww_data = await scrape_awwwards(pages=5)

    combined = pd.concat([lapa_data, aww_data], ignore_index=True)
    combined_path = Path("data/combined_designs.csv")
    combined.to_csv(combined_path, index=False)

    print(f"🎉 Combined dataset saved → {combined_path}")
    print(f"✅ Total templates scraped: {len(combined)}")


if __name__ == "__main__":
    asyncio.run(main())