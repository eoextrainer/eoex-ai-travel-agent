#!/usr/bin/env python3
import os
import json
from amadeus import Client, ResponseError
from datetime import datetime, timedelta
import time

# Load credentials from environment
CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in environment (source .env)")
    raise SystemExit(1)

HOST = (os.getenv("AMADEUS_HOST", "test").lower())
if HOST in ("production", "prod"):
    amadeus = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, host='production')
else:
    amadeus = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
PREFERRED_CITY_CODES = {
    "Paris": "PAR",
    "Athens": "ATH",
    "Madrid": "MAD",
    "Moscow": "MOW",
    "Beijing": "BJS",
    "London": "LON",
    "Rome": "ROM",
}

# Helpers: resolve multiple codes and perform resilient search

def resolve_codes(city_name: str) -> tuple[str | None, list[str]]:
    city_code = None
    airport_codes: list[str] = []
    try:
        resp_city = amadeus.reference_data.locations.cities.get(keyword=city_name)
        data_city = resp_city.data if isinstance(resp_city.data, list) else []
        if data_city:
            # Prefer explicit mapping when ambiguous
            city_code = PREFERRED_CITY_CODES.get(city_name) or data_city[0].get("iataCode")
    except ResponseError:
        pass
    try:
        resp_air = amadeus.reference_data.locations.get(keyword=city_name, subType="AIRPORT")
        data_air = resp_air.data if isinstance(resp_air.data, list) else []
        for item in data_air:
            code = item.get("iataCode") or (item.get("address") or {}).get("iataCode")
            if code:
                airport_codes.append(code)
        # Stable preference: ensure preferred code (if any) is first
        preferred = PREFERRED_CITY_CODES.get(city_name)
        if preferred and preferred in airport_codes:
            airport_codes = [preferred] + [c for c in airport_codes if c != preferred]
    except ResponseError:
        pass
    return city_code, airport_codes


def try_flight_offers(origin_code: str, dest_code: str, date_str: str, adults: int = 1, max_retries: int = 2):
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_code,
                destinationLocationCode=dest_code,
                departureDate=date_str,
                adults=adults,
            )
            data = resp.data if isinstance(resp.data, list) else []
            return data
        except ResponseError as e:
            last_err = e
            # Exponential backoff on provider 5xx
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status and int(status) >= 500 and attempt < max_retries - 1:
                time.sleep(0.6 * (2 ** attempt))
                continue
            break
    raise last_err


def fallback_dates(origin_code: str, dest_code: str) -> list[str]:
    try:
        resp = amadeus.shopping.flight_dates.get(origin=origin_code, destination=dest_code)
        data = resp.data if isinstance(resp.data, list) else []
        dates: list[str] = []
        for item in data:
            d = item.get("departureDate") or item.get("date")
            if isinstance(d, str):
                dates.append(d)
        return dates
    except ResponseError:
        return []


def resilient_search(origin_city: str, dest_city: str, date_str: str):
    # Resolve codes and build attempt pairs
    o_city, o_airports = resolve_codes(origin_city)
    d_city, d_airports = resolve_codes(dest_city)
    attempts: list[tuple[str, str]] = []
    if o_city and d_city:
        attempts.append((o_city, d_city))
    if o_airports and d_airports:
        attempts.append((o_airports[0], d_airports[0]))
    if o_city and d_airports:
        attempts.append((o_city, d_airports[0]))
    if o_airports and d_city:
        attempts.append((o_airports[0], d_city))

    # Try attempts with requested date
    for o_code, d_code in attempts:
        try:
            data = try_flight_offers(o_code, d_code, date_str)
            if data:
                return data, {"origin": o_code, "dest": d_code, "date": date_str, "fallback": False}
        except ResponseError as e:
            # If provider error, try fallback dates
            pass

    # Fallback: query available dates and try nearest to requested
    for o_code, d_code in attempts:
        dates = fallback_dates(o_code, d_code)
        if not dates:
            continue
        try_dates = []
        # Prefer exact or close dates around requested
        try:
            req_dt = datetime.strptime(date_str, "%Y-%m-%d")
            # sort by proximity
            try_dates = sorted(dates, key=lambda s: abs((datetime.strptime(s, "%Y-%m-%d") - req_dt).days))
        except Exception:
            try_dates = dates
        for d in try_dates[:3]:  # try up to 3 dates
            try:
                data = try_flight_offers(o_code, d_code, d)
                if data:
                    return data, {"origin": o_code, "dest": d_code, "date": d, "fallback": True}
            except ResponseError:
                continue

    # Final fallback: no data, return empty with meta
    return [], {"origin": attempts[0][0] if attempts else None, "dest": attempts[0][1] if attempts else None, "date": date_str, "fallback": True}

# Searches: 10 city-to-city with dates
searches = [
    ("Paris", "Athens", "2026-01-01"),
    ("Athens", "Madrid", "2026-01-02"),
    ("Madrid", "Moscow", "2026-01-03"),
    ("Moscow", "Beijing", "2026-01-04"),
    ("Paris", "Madrid", "2026-01-05"),
    ("Madrid", "Paris", "2026-01-06"),
    ("Athens", "Beijing", "2026-01-07"),
    ("Moscow", "Athens", "2026-01-08"),
    ("London", "Rome", "2026-01-09"),
    ("Rome", "Madrid", "2026-01-10"),
]

for origin_city, dest_city, date in searches:
    data, meta = resilient_search(origin_city, dest_city, date)
    sample_price = None
    if data:
        try:
            sample_price = data[0].get("price", {}).get("total")
        except Exception:
            sample_price = None
    # Always print a consistent output; avoid provider_error spam
    print(
        f"{origin_city} -> {dest_city} {date} result=count={len(data)} sample_price={sample_price} used_origin={meta.get('origin')} used_dest={meta.get('dest')} used_date={meta.get('date')} fallback={meta.get('fallback')}"
    )
