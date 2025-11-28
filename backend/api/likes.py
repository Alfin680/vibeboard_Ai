from fastapi import APIRouter, Body
from backend.db.supabase_client import supabase

router = APIRouter()

@router.post("/likes/add")
def add_like(
    user_id: str = Body(...),
    title: str = Body(...),
    url: str = Body(...),
    image: str = Body(...),
    caption: str = Body(None),
):
    data = {
        "user_id": user_id,
        "title": title,
        "url": url,
        "image": image,
        "caption": caption,
    }

    # UPSERT
    response = supabase.table("liked_vibes").upsert(data).execute()

    return {"status": "success", "data": response.data}


@router.post("/likes/remove")
def remove_like(
    user_id: str = Body(...),
    url: str = Body(...),
):
    response = (
        supabase.table("liked_vibes")
        .delete()
        .eq("user_id", user_id)
        .eq("url", url)
        .execute()
    )
    return {"status": "deleted", "data": response.data}


@router.get("/likes/{user_id}")
def get_likes(user_id: str):
    response = (
        supabase.table("liked_vibes")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return {"items": response.data}
