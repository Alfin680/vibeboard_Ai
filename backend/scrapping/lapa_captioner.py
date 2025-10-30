from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(device)

def generate_caption(image_url: str) -> str:
    """
    Takes an image URL and returns a descriptive caption using BLIP.
    """
    try:
        raw_image = Image.open(requests.get(image_url, stream=True).raw).convert('RGB')
        inputs = processor(raw_image, return_tensors="pt").to(device)
        out = model.generate(**inputs, max_length=30)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        return f"Error generating caption: {e}"
if __name__ == "__main__":
    # Example test image from Lapa Ninja
    test_url = "https://cdn.lapa.ninja/assets/templates/last-studio-framer-template-thumb.jpg"
    print("Generating caption for:", test_url)
    caption = generate_caption(test_url)
    print("📝 Caption:", caption)
