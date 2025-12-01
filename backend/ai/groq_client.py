import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY missing in environment")
    return Groq(api_key=key)

groq_client = get_groq_client()
