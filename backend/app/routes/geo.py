from fastapi import APIRouter, Query
from sqlalchemy import text
from ..db import engine
import os, json, csv

router = APIRouter()

REGION_FILES = [
    "africa.json","america.json","asia.json","pacific.json","indian.json",
    "europe.json","atlantic.json","australia.json","arctic.json"
]

def _fit(s: str, n: int = 255) -> str:
    return (s or "")[:n]

@router.post("/seed-regions")


def seed_regions(dirPath: str = Query("/app/doc/")):
    with engine.begin() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM cities"))
        conn.execute(text("DELETE FROM countries"))
        conn.execute(text("DELETE FROM regions"))
        # Insert regions from list
        regions_map = {}
        for rf in REGION_FILES:
            name = rf.split(".")[0].capitalize() if rf != 'america.json' else 'America'
            conn.execute(text("INSERT INTO regions (name) VALUES (:n)"), {"n": name})
        rows = conn.execute(text("SELECT id,name FROM regions")).mappings().all()
        regions_map = {r['name']: r['id'] for r in rows}

        # For each region file, parse and insert countries/cities
        for rf in os.listdir(dirPath):
            if not rf.endswith('.csv'):
                continue
            region_name = rf.split(".")[0].capitalize() if rf != 'america.csv' else 'America'
            rid = regions_map.get(region_name)
            if not rid:
                continue
            path = os.path.join(dirPath, rf)
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    debug_rows = []
                    for i, row in enumerate(reader):
                        if i < 5:
                            debug_rows.append(dict(row))
                        country_name = _fit(row.get('Country name EN') or row.get('country') or row.get('Country') or region_name)
                        city_name = _fit(row.get('Name') or row.get('name'))
                        if not country_name or not city_name:
                            continue
                        conn.execute(text("INSERT IGNORE INTO countries (region_id, name) VALUES (:rid, :n)"), {"rid": rid, "n": country_name})
                        crow = conn.execute(text("SELECT id FROM countries WHERE region_id=:rid AND name=:n"), {"rid": rid, "n": country_name}).fetchone()
                        if not crow:
                            continue
                        country_id = int(crow[0])
                        conn.execute(text("INSERT IGNORE INTO cities (country_id, name, is_capital) VALUES (:cid, :n, 0)"), {"cid": country_id, "n": city_name})
                    print(f"[DEBUG] First 5 rows from {rf}: {debug_rows}")
            except Exception as e:
                print(f"[ERROR] Failed to parse {rf}: {e}")
    return {"status": "seeded"}


@router.get("/regions")
def list_regions():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name FROM regions ORDER BY name")).mappings().all()
        return [{"id": r['id'], "name": r['name']} for r in rows]


@router.get("/countries")
def list_countries(region_id: int = Query(...)):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name FROM countries WHERE region_id = :rid ORDER BY name"), {"rid": region_id}).mappings().all()
        return [{"id": r['id'], "name": r['name']} for r in rows]


@router.get("/cities")
def list_cities(country_id: int = Query(...)):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, is_capital FROM cities WHERE country_id = :cid ORDER BY is_capital DESC, name"), {"cid": country_id}).mappings().all()
        return [{"id": r['id'], "name": r['name'], "is_capital": int(r['is_capital'])} for r in rows]

@router.get("/dump")
def dump_geo():
    with engine.connect() as conn:
        regions = conn.execute(text("SELECT id, name FROM regions ORDER BY name")).mappings().all()
        countries = conn.execute(text("SELECT id, region_id, name FROM countries ORDER BY name")).mappings().all()
        cities = conn.execute(text("SELECT id, country_id, name, is_capital FROM cities ORDER BY name")).mappings().all()
        return {
            "regions": [{"id": r["id"], "name": r["name"]} for r in regions],
            "countries": [{"id": c["id"], "region_id": c["region_id"], "name": c["name"]} for c in countries],
            "cities": [{"id": c["id"], "country_id": c["country_id"], "name": c["name"], "is_capital": int(c["is_capital"]) } for c in cities],
        }
