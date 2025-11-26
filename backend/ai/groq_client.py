
from groq import Groq
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
