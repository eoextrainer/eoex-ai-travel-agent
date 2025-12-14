from fastapi import APIRouter, Query
from sqlalchemy import text
from ..db import engine

router = APIRouter()

# Static seed data
SEED_CONTINENTS = ['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania', 'Antarctica']
SEED_COUNTRIES = {
    'Europe': ['France', 'Germany', 'Greece', 'Italy', 'Spain', 'United Kingdom'],
    'Asia': ['Japan', 'China', 'India', 'South Korea', 'Thailand'],
    'North America': ['United States', 'Canada', 'Mexico'],
    'South America': ['Brazil', 'Argentina', 'Chile', 'Peru'],
    'Africa': ['South Africa', 'Nigeria', 'Egypt', 'Kenya'],
    'Oceania': ['Australia', 'New Zealand'],
    'Antarctica': []
}
SEED_CAPITALS = {
    'France': 'Paris', 'Germany': 'Berlin', 'Greece': 'Athens', 'Italy': 'Rome', 'Spain': 'Madrid', 'United Kingdom': 'London',
    'United States': 'Washington, D.C.', 'Canada': 'Ottawa', 'Mexico': 'Mexico City',
    'Japan': 'Tokyo', 'China': 'Beijing', 'India': 'New Delhi', 'South Korea': 'Seoul', 'Thailand': 'Bangkok',
    'Brazil': 'Brasília', 'Argentina': 'Buenos Aires', 'Chile': 'Santiago', 'Peru': 'Lima',
    'South Africa': 'Pretoria', 'Nigeria': 'Abuja', 'Egypt': 'Cairo', 'Kenya': 'Nairobi',
    'Australia': 'Canberra', 'New Zealand': 'Wellington'
}

@router.post("/seed")
def seed_geo():
    with engine.begin() as conn:
        # Insert continents
        for c in SEED_CONTINENTS:
            conn.execute(text("INSERT IGNORE INTO continents (name) VALUES (:name)"), {"name": c})
        # Map continent names to ids
        cont_rows = conn.execute(text("SELECT id, name FROM continents")).mappings().all()
        cont_map = {r['name']: r['id'] for r in cont_rows}  # type: ignore
        # Insert countries
        for cont, countries in SEED_COUNTRIES.items():
            cid = cont_map.get(cont)
            if not cid:
                continue
            for country in countries:
                conn.execute(text("INSERT IGNORE INTO countries (continent_id, name) VALUES (:cid, :name)"), {"cid": cid, "name": country})
        # Map country names to ids
        rows = conn.execute(text("SELECT c.id as id, c.name as name FROM countries c")).mappings().all()
        country_map = {r['name']: r['id'] for r in rows}  # type: ignore
        # Insert capitals
        for country, capital in SEED_CAPITALS.items():
            cid = country_map.get(country)
            if cid:
                conn.execute(text("INSERT IGNORE INTO capitals (country_id, name) VALUES (:cid, :name)"), {"cid": cid, "name": capital})
    return {"status": "seeded"}

@router.get("/continents")
def list_continents():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name FROM continents ORDER BY name")).mappings().all()
        return [r['name'] for r in rows]

@router.get("/countries")
def list_countries(continent: str = Query(...)):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT c.name FROM countries c JOIN continents ct ON ct.id = c.continent_id WHERE ct.name = :cont ORDER BY c.name"), {"cont": continent}).mappings().all()
        return [r['name'] for r in rows]

@router.get("/capitals")
def list_capitals(country: str = Query(...)):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT cp.name FROM capitals cp JOIN countries c ON c.id = cp.country_id WHERE c.name = :country ORDER BY cp.name"), {"country": country}).mappings().all()
        return [r['name'] for r in rows]

@router.get("/dump")
def dump_geo():
    """Return all continents, countries, and capitals for debugging/wiring verification."""
    with engine.connect() as conn:
        continents = conn.execute(text("SELECT id, name FROM continents ORDER BY name")).mappings().all()
        countries = conn.execute(text("SELECT id, continent_id, name FROM countries ORDER BY name")).mappings().all()
        capitals = conn.execute(text("SELECT id, country_id, name FROM capitals ORDER BY name")).mappings().all()
        return {
            "continents": [{"id": c["id"], "name": c["name"]} for c in continents],
            "countries": [{"id": c["id"], "continent_id": c["continent_id"], "name": c["name"]} for c in countries],
            "capitals": [{"id": c["id"], "country_id": c["country_id"], "name": c["name"]} for c in capitals],
        }
