import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
# =========================
# SETTINGS
# =========================
load_dotenv()
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "captioned_designs.csv"
OUTPUT_FILE = DATA_DIR / "tagged_designs.csv"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# TAG GENERATION FUNCTION
# =========================
def generate_tags(title, caption, source):
    """
    Use OpenAI to generate 3–6 descriptive tags (comma-separated).
    """
    try:
        prompt = f"""
        You are a design curator. Based on the following website info, suggest 3–6 concise descriptive tags.
        Tags should capture the website's style, purpose, and vibe (e.g., 'Portfolio', 'Minimal', 'Agency', 'Ecommerce', 'Bold').

        Website Source: {source}
        Title: {title}
        Caption: {caption}

        Format your answer as a comma-separated list only, no numbering or extra text.
        Example: Portfolio, Minimal, Agency, Clean Design
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        tags = response.output_text.strip()
        return tags

    except Exception as e:
        print(f"⚠️ Error generating tags: {e}")
        return ""


# =========================
# MAIN SCRIPT
# =========================
def main():
    print("🏷️ Generating tags using OpenAI...")
    df = pd.read_csv(INPUT_FILE)
    tags_list = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        title = row.get("title", "")
        caption = row.get("ai_caption", "")
        source = row.get("source", "")
        tags = generate_tags(title, caption, source)
        tags_list.append(tags)

    df["ai_tags"] = tags_list
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved tagged dataset → {OUTPUT_FILE}")
    print(f"✅ Total designs tagged: {len(df)}")


if __name__ == "__main__":
    main()
