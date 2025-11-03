import pandas as pd

# File paths
input_path = "data/combined_designs.csv"
output_path = "data/cleaned_designs.csv"

# Load dataset
df = pd.read_csv(input_path)
print(f"Original dataset size: {len(df)}")

# Drop rows missing image or URL
df = df.dropna(subset=["image", "url"])
print(f"After removing rows with missing image or URL: {len(df)}")

# Clean and normalize string columns (if they exist)
for col in ["tags", "ai_tags", "ai_caption"]:
    if col in df.columns:
        df[col] = df[col].fillna("").apply(
            lambda x: ", ".join([t.strip().lower() for t in str(x).split(",") if t.strip()])
        )
    else:
        print(f" Column '{col}' not found, skipping normalization.")

# Remove duplicate URLs
df = df.drop_duplicates(subset=["url"])
print(f"After removing duplicate URLs: {len(df)}")

# Reset index and save
df = df.reset_index(drop=True)
df.to_csv(output_path, index=False)
print(f" Cleaned dataset saved to {output_path}")
print(f"Final dataset size: {len(df)}")
