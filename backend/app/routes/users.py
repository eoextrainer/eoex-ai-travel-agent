from fastapi import APIRouter

router = APIRouter()

@router.get("/default")
def get_default_user():
    return {"username": "traveler-1", "role": "user"}
