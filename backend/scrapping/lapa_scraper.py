import asyncio
import csv
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def scrape_lapaninja():
    url = "https://www.lapa.ninja/templates/"
    scraped = []

    print(f"🌐 Opening {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # ✅ Use domcontentloaded instead of networkidle
        await page.goto(url, wait_until="domcontentloaded")

        try:
            # Wait for any template card to appear
            await page.wait_for_selector("div.bg-white.rounded-lg", timeout=20000)
        except PlaywrightTimeoutError:
            print("⚠️ Warning: Timeout waiting for cards to appear. Continuing anyway...")

        print("🔄 Scrolling to load all templates...")

        # Scroll down until page stops changing height
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

        print("✅ Reached end of page.")

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.bg-white.rounded-lg.shadow-sm.border")

    print(f"✅ Found {len(cards)} cards.")

    for card in cards:
        title = card.select_one("h3.font-semibold")
        author = card.select_one("p.text-sm")
        price = card.select_one("span.text-lg.font-bold")
        img = card.select_one("img")
        tags = [t.get_text(strip=True) for t in card.select("a[class*='inline-flex']")]
        link = card.select_one("a[href*='/templates/']")

        scraped.append({
            "title": title.get_text(strip=True) if title else "",
            "author": author.get_text(strip=True) if author else "",
            "price": price.get_text(strip=True) if price else "",
            "tags": ", ".join(tags) if tags else "",
            "image": img["src"].strip() if img and img.has_attr("src") else "",
            "url": (
                f"https://www.lapa.ninja{link['href'].strip()}"
                if link and link.has_attr("href") and link['href'].startswith("/")
                else (link['href'].strip() if link and link.has_attr("href") else "")
            )
        })

    if scraped:
        file_path = "backend/scrapping/data/raw_lapaninja_designs.csv"
        print(f"💾 Saving {len(scraped)} entries to {file_path}")

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=scraped[0].keys())
            writer.writeheader()
            writer.writerows(scraped)

        print("🎉 Scraping complete!")
    else:
        print("⚠️ No cards were scraped. Try increasing timeout or checking site structure.")

if __name__ == "__main__":
    asyncio.run(scrape_lapaninja())
