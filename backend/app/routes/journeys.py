from fastapi import APIRouter, HTTPException
from ..db import engine
from sqlalchemy import text
from typing import Dict, Any

router = APIRouter()

@router.get("")
def list_journeys():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, user_id, destination_country, destination_city, budget, created_at FROM journeys ORDER BY created_at DESC LIMIT 50")).mappings().all()
        return [dict(r) for r in rows]

@router.post("/seed")
def seed_journey(payload: Dict[str, Any]):
    required = ["user_id", "destination_country", "destination_city", "budget"]
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {k}")
    with engine.begin() as conn:
        res = conn.execute(text(
            "INSERT INTO journeys (user_id, destination_country, destination_city, budget) VALUES (:user_id, :destination_country, :destination_city, :budget)"
        ), payload)
        journey_id = res.lastrowid
        # Optionally seed related tables if present in payload
        for item in payload.get("flights", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO flights (journey_id, airline, origin_city, destination_city, departure_date, arrival_date, price) VALUES (:journey_id, :airline, :origin_city, :destination_city, :departure_date, :arrival_date, :price)"
            ), item)
        for item in payload.get("accommodations", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO accommodations (journey_id, name, address, city, price_per_night) VALUES (:journey_id, :name, :address, :city, :price_per_night)"
            ), item)
        for item in payload.get("transportation", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO transportation (journey_id, type, provider, price) VALUES (:journey_id, :type, :provider, :price)"
            ), item)
        for item in payload.get("food_choices", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO food_choices (journey_id, restaurant, cuisine, price_range) VALUES (:journey_id, :restaurant, :cuisine, :price_range)"
            ), item)
        for item in payload.get("shopping_choices", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO shopping_choices (journey_id, shop_name, category, price_range) VALUES (:journey_id, :shop_name, :category, :price_range)"
            ), item)
        for item in payload.get("places_to_visit", []):
            item["journey_id"] = journey_id
            conn.execute(text(
                "INSERT INTO places_to_visit (journey_id, place_name, category, description) VALUES (:journey_id, :place_name, :category, :description)"
            ), item)
        # Stub data if missing
        if not payload.get("transportation"):
            conn.execute(text(
                "INSERT INTO transportation (journey_id, type, provider, price) VALUES (:journey_id, :type, :provider, :price)"
            ), {"journey_id": journey_id, "type": "Metro", "provider": "City Transit", "price": 15.0})
        if not payload.get("food_choices"):
            conn.execute(text(
                "INSERT INTO food_choices (journey_id, restaurant, cuisine, price_range) VALUES (:journey_id, :restaurant, :cuisine, :price_range)"
            ), {"journey_id": journey_id, "restaurant": "Local Bistro", "cuisine": "Mediterranean", "price_range": "$$"})
        if not payload.get("shopping_choices"):
            conn.execute(text(
                "INSERT INTO shopping_choices (journey_id, shop_name, category, price_range) VALUES (:journey_id, :shop_name, :category, :price_range)"
            ), {"journey_id": journey_id, "shop_name": "Central Mall", "category": "General", "price_range": "$$$"})
    return {"journey_id": journey_id}
