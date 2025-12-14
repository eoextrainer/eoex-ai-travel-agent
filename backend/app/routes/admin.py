from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
def admin_dashboard(user: str | None = None, destination: str | None = None, budget: float | None = None):
    return {"filters": {"user": user, "destination": destination, "budget": budget}, "results": []}
