import os
from fastapi.testclient import TestClient
from backend.app.main import app


def setup_module():
    os.environ.setdefault("MYSQL_USER", "eoex")
    os.environ.setdefault("MYSQL_PASSWORD", "eoex")
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_DB", "eoex_travel")


client = TestClient(app)


def test_manual_seeding_and_admin_dashboard():
    payload = {
        "user_id": 1,
        "destination_country": "Greece",
        "destination_city": "Athens",
        "budget": 2000.0,
        "flights": [
            {
                "airline": "BA",
                "origin_city": "MAD",
                "destination_city": "ATH",
                "departure_date": "2026-01-15",
                "arrival_date": "2026-01-15",
                "price": 250.00,
            }
        ],
        "accommodations": [
            {
                "name": "Hotel Athens",
                "address": "1 Main St",
                "city": "Athens",
                "price_per_night": 120.00,
            }
        ],
    }

    # Seed journey
    r = client.post("/api/journeys/seed", json=payload)
    assert r.status_code in (200, 201)

    # Verify journeys endpoint returns at least one row
    jr = client.get("/api/journeys")
    assert jr.status_code == 200
    rows = jr.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1

    # Verify admin dashboard filter
    ar = client.get(
        "/api/admin/dashboard",
        params={"user": "traveler-1", "destination": "Athens", "budget": 2500},
    )
    assert ar.status_code == 200
    results = ar.json()
    assert isinstance(results, list)
    assert len(results) >= 1