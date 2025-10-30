import os
import pandas as pd
from openai import OpenAI
from lapa_captioner import generate_caption

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RAW_CSV = "data/raw_lapaninja_designs.csv"
OUTPUT_CSV = "data/ai_tagged_lapaninja.csv"

def generate_tags_with_gpt(caption: str):
    """Ask GPT to generate structured tags + category from the caption."""
    prompt = f"""
    You are an AI web design analyst.
    Based on the following design description, generate relevant structured metadata:
    - 5 to 10 descriptive tags
    - 1 main category (like Portfolio, SaaS, Agency, Product, Creative, Minimal, etc.)

    Design Description:
    "{caption}"

    Format your output as JSON like this:
    {{
        "tags": ["tag1", "tag2", "tag3"],
        "category": "CategoryName"
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    try:
        import json
        data = json.loads(response.choices[0].message.content)
        return data.get("tags", []), data.get("category", "")
    except Exception:
        return [], ""

def main():
    df = pd.read_csv(RAW_CSV)

    if "image_url" not in df.columns:
        print("❌ No 'image_url' column found in CSV!")
        return

    tagged_data = []
    for idx, row in df.iterrows():
        print(f"\n🖼️  Processing {idx+1}/{len(df)}: {row.get('title', 'Untitled')}")
        image_url = row["image_url"]

        # Step 1: Generate caption
        caption = generate_caption(image_url)
        print("   ✏️ Caption:", caption)

        # Step 2: Generate tags + category
        tags, category = generate_tags_with_gpt(caption)
        print("   🏷️ Tags:", tags)
        print("   📂 Category:", category)

        tagged_data.append({
            "title": row.get("title"),
            "url": row.get("url"),
            "image_url": image_url,
            "caption": caption,
            "tags": ", ".join(tags),
            "category": category
        })

    # Save to new CSV
    out_df = pd.DataFrame(tagged_data)
    os.makedirs("data", exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n🎉 AI tagging complete! Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
