from fastapi import APIRouter, Query
from sqlalchemy import text
from ..db import engine

router = APIRouter()

@router.get("/dashboard")
def admin_dashboard(
    user: str | None = Query(None),
    destination: str | None = Query(None),
    budget: float | None = Query(None),
):
    query = """
        SELECT j.id, u.username, j.destination_country, j.destination_city, j.budget, j.created_at
        FROM journeys j
        JOIN users u ON u.id = j.user_id
        WHERE ( :user IS NULL OR u.username = :user )
          AND ( :destination IS NULL OR j.destination_city = :destination OR j.destination_country = :destination )
          AND ( :budget IS NULL OR j.budget <= :budget )
        ORDER BY j.created_at DESC
        LIMIT 100
    """
    with engine.connect() as conn:
        rows = conn.execute(text(query), {"user": user, "destination": destination, "budget": budget}).mappings().all()
        return [dict(r) for r in rows]
