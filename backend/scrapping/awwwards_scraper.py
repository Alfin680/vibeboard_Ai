from playwright.sync_api import sync_playwright
import pandas as pd
import time, os

def scrape_awwwards(pages=3):
    all_data = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        for i in range(1, pages + 1):
            url = f"https://www.awwwards.com/websites/?page={i}"
            print(f"🌐 Scraping page {i}: {url}")
            page.goto(url, timeout=60000)
            page.wait_for_selector("div.card-site", timeout=30000)

            cards = page.query_selector_all("div.card-site")
            print(f"✅ Found {len(cards)} cards on page {i}")

            for card in cards:
                try:
                    title = card.query_selector(".figure-rollover__row:nth-child(2)")
                    title = title.inner_text().strip() if title else None

                    img = card.query_selector("figure img")
                    img_url = None
                    if img:
                        srcset = img.get_attribute("data-srcset") or img.get_attribute("srcset")
                        if srcset:
                            img_url = srcset.split(" ")[0]

                    author = card.query_selector(".avatar-name__title")
                    author = author.inner_text().strip() if author else None

                    tag = card.query_selector(".budget-tag")
                    tag = tag.inner_text().strip() if tag else None

                    external_link = card.query_selector(".figure-rollover__bts a")
                    external_link = external_link.get_attribute("href") if external_link else None

                    print(f"\n--- CARD ---")
                    print(f"Title: {title}")
                    print(f"Image: {img_url}")
                    print(f"Author: {author}")
                    print(f"Tag: {tag}")
                    print(f"External: {external_link}")

                    # Append even if partial (to see what's missing)
                    all_data.append({
                        "title": title,
                        "author": author,
                        "tag": tag,
                        "image_url": img_url,
                        "external_link": external_link
                    })

                except Exception as e:
                    print(f"⚠️  Error on a card: {e}")

            time.sleep(2)

        browser.close()

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(all_data)
    df.to_csv("data/raw_awwwards_designs.csv", index=False)
    print(f"🎉 Scraping complete! Saved {len(all_data)} entries to data/raw_awwwards_designs.csv")

if __name__ == "__main__":
    scrape_awwwards(pages=10)
