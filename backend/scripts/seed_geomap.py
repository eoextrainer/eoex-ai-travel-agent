#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from db import engine  # noqa: E402


def _fit_name(val: str, maxlen: int = 64) -> str:
    if not isinstance(val, str):
        val = str(val)
    return val[:maxlen]


def get_or_create_continent(conn, name: str) -> int:
    name = _fit_name(name)
    row = conn.execute(text("SELECT id FROM continents WHERE name=:n"), {"n": name}).fetchone()
    if row:
        return int(row[0])
    conn.execute(text("INSERT INTO continents (name) VALUES (:n)"), {"n": name})
    row = conn.execute(text("SELECT id FROM continents WHERE name=:n"), {"n": name}).fetchone()
    return int(row[0])


def get_or_create_country(conn, continent_id: int, name: str) -> int:
    name = _fit_name(name)
    row = conn.execute(text("SELECT id FROM countries WHERE continent_id=:cid AND name=:n"), {"cid": continent_id, "n": name}).fetchone()
    if row:
        return int(row[0])
    conn.execute(text("INSERT INTO countries (continent_id, name) VALUES (:cid, :n)"), {"cid": continent_id, "n": name})
    row = conn.execute(text("SELECT id FROM countries WHERE continent_id=:cid AND name=:n"), {"cid": continent_id, "n": name}).fetchone()
    return int(row[0])


def get_or_create_capital(conn, country_id: int, name: str) -> int:
    name = _fit_name(name)
    row = conn.execute(text("SELECT id FROM capitals WHERE country_id=:coid AND name=:n"), {"coid": country_id, "n": name}).fetchone()
    if row:
        return int(row[0])
    conn.execute(text("INSERT INTO capitals (country_id, name) VALUES (:coid, :n)"), {"coid": country_id, "n": name})
    row = conn.execute(text("SELECT id FROM capitals WHERE country_id=:coid AND name=:n"), {"coid": country_id, "n": name}).fetchone()
    return int(row[0])


KNOWN_CONTINENTS = {"Africa", "Antarctica", "Asia", "Europe", "North America", "South America", "Oceania"}


def seed_from_geomap(json_path: Path) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"geomap.json not found at {json_path}")
    data = json.loads(json_path.read_text())

    continents_in = data.get('continents') if isinstance(data, dict) else data
    stats = {"continents": 0, "countries": 0, "capitals": 0, "cities": 0}
    with engine.begin() as conn:
        # Normalize input into a standard iterable of continent objects
        normalized_conts = []
        if isinstance(continents_in, list):
            normalized_conts = continents_in
        elif isinstance(continents_in, dict):
            for name, payload in continents_in.items():
                normalized_conts.append({"name": name, **(payload if isinstance(payload, dict) else {})})

        for cont in normalized_conts:
            if not isinstance(cont, dict):
                continue
            cont_name = cont.get('name') or cont.get('continent')
            if not cont_name:
                continue
            # Only seed known 7 continents
            if cont_name not in KNOWN_CONTINENTS:
                continue
            cont_id = get_or_create_continent(conn, cont_name)
            stats["continents"] += 1

            countries = cont.get('countries')
            # countries may be dict mapping country -> {capital, cities}
            if isinstance(countries, dict):
                items = countries.items()
            elif isinstance(countries, list):
                items = []
                for c in countries:
                    if isinstance(c, dict):
                        items.append((c.get('name') or c.get('country'), {"capital": c.get('capital'), "cities": c.get('cities') or []}))
            else:
                items = []

            for country_name, payload in items:
                if not country_name:
                    continue
                country_id = get_or_create_country(conn, cont_id, country_name)
                stats["countries"] += 1
                capital_name = None
                cities_list = []
                if isinstance(payload, dict):
                    capital_name = payload.get('capital')
                    cities_list = payload.get('cities') or []
                if capital_name:
                    get_or_create_capital(conn, country_id, capital_name)
                    stats["capitals"] += 1
                # Insert cities
                for city in cities_list:
                    if not city:
                        continue
                    city = _fit_name(city)
                    conn.execute(text("INSERT IGNORE INTO cities (country_id, name) VALUES (:cid, :n)"), {"cid": country_id, "n": city})
                    stats["cities"] += 1
    return stats


def main():
    base = Path(__file__).resolve().parents[2]
    default_path = base / 'docs' / 'doc' / 'geomap.json'
    target = Path(os.getenv('GEOMAP_JSON_PATH', str(default_path)))
    try:
        stats = seed_from_geomap(target)
        print(f"Seeded: continents={stats['continents']} countries={stats['countries']} capitals={stats['capitals']}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
