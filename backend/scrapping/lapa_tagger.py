import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found. Make sure your .env file is named '.env' (not .env.txt) and contains:\nOPENAI_API_KEY=your_key_here")

client = OpenAI(api_key=api_key)

# ✅ Path to your CSV file (adjust if needed)
csv_path = os.path.join(os.path.dirname(__file__), "data", "raw_lapaninja_designs.csv")

# ✅ Read CSV
df = pd.read_csv(csv_path)
print(f"✅ Loaded {len(df)} designs from raw_lapaninja_designs.csv")

# ✅ Column check
if "image" not in df.columns and "image_url" not in df.columns:
    raise ValueError("❌ No 'image' or 'image_url' column found in CSV!")

# ✅ Add a new column for AI-generated captions
captions = []

for i, row in df.iterrows():
    image_url = row.get("image") or row.get("image_url")
    title = row.get("title", "")
    tags = row.get("tags", "")

    print(f"🖼️ Generating caption for: {title}")

    prompt = f"""
    You are an expert web design analyst. Describe the visual design style and mood of this template briefly.
    Template title: {title}
    Tags: {tags}
    Image: {image_url}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create short, catchy, descriptive captions for website templates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        caption = response.choices[0].message.content.strip()
        print(f"✨ Caption: {caption}")
    except Exception as e:
        print(f"⚠️ Error processing {title}: {e}")
        caption = ""

    captions.append(caption)

# ✅ Save to new CSV
df["ai_caption"] = captions
output_path = os.path.join(os.path.dirname(__file__), "data", "tagged_lapaninja_designs.csv")
df.to_csv(output_path, index=False)

print(f"\n💾 Saved tagged data to {output_path}")
