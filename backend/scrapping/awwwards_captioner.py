import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_caption(image_url: str) -> str:
    """
    Uses GPT-4o-mini to generate a short creative caption describing
    the design, style, and mood of the given Awwwards website image.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a design critic who writes concise, visual-style captions."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this web design image from Awwwards. "
                                "Describe it in 1–2 sentences focusing on mood, style, and color tone."
                            )
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )

        caption = response.choices[0].message.content.strip()
        return caption
    except Exception as e:
        print(f"⚠️ Error generating caption: {e}")
        return ""

if __name__ == "__main__":
    # Example test image
    test_image = "https://assets.awwwards.com/awards/images/2023/01/example-website.jpg"
    caption = generate_caption(test_image)
    print("🖼️ Caption:", caption)
