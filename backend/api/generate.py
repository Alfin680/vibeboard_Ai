# backend/api/generate.py (Revised)

from fastapi import APIRouter
from backend.ai.groq_client import groq_client

router = APIRouter()

@router.get("/generate-idea")
async def generate_idea():
    # ----------------------------------------------------
    # 🚀 The optimized single-line prompt:
    # ----------------------------------------------------
    prompt = """Generate a single website UI concept, 6 words maximum. Focus only on style, color, and mood. Example: Calm, minimalist dashboard with soft gradients.,"Minimalist fintech dashboard with soft gradients",
                Luxury eCommerce landing page with serif typography,
                Vibrant portfolio site with animated transitions,
                Dark-mode SaaS interface with neon accents,
                Calm wellness app UI with pastel colors"""
    try:
        completion = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)


        idea = completion.choices[0].message.content.strip()

        return {"idea": idea}

    except Exception as e:
        print("GROQ ERROR:", e)
        return {"idea": None, "error": str(e)}