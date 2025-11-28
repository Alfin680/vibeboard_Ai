from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/search")
async def search(query: str = Query(...)):
    return {
        "results": [
            {
                "image": "https://picsum.photos/seed/1/400/300",
                "caption": f"Design direction inspired by: {query}"
            },
            {
                "image": "https://picsum.photos/seed/2/400/300",
                "caption": f"Modern layout generated from: {query}"
            },
            {
                "image": "https://picsum.photos/seed/3/400/300",
                "caption": f"Creative UI exploration for: {query}"
            },
        ]
    }
