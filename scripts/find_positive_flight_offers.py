#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime, timedelta
from amadeus import Client, ResponseError


def env_credentials() -> Client:
    cid = os.getenv("AMADEUS_CLIENT_ID")
    sec = os.getenv("AMADEUS_CLIENT_SECRET")
    host_env = os.getenv("AMADEUS_HOST", "test").lower()
    if not cid or not sec:
        print("ERROR: Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in environment (source .env)")
        sys.exit(1)
    if host_env in ("production", "prod"):
        return Client(client_id=cid, client_secret=sec, host='production')
    return Client(client_id=cid, client_secret=sec)


def retry_call(fn, max_retries=2, base_sleep=0.6):
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn()
        except ResponseError as e:
            last_err = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status and int(status) >= 500 and attempt < max_retries - 1:
                time.sleep(base_sleep * (2 ** attempt))
                continue
            break
    raise last_err


def get_airports(amadeus: Client, keyword: str) -> list[str]:
    try:
        resp = retry_call(lambda: amadeus.reference_data.locations.get(keyword=keyword, subType="AIRPORT"))
        data = resp.data if isinstance(resp.data, list) else []
        codes = []
        for item in data:
            code = item.get("iataCode") or (item.get("address") or {}).get("iataCode")
            if code:
                codes.append(code)
        return codes
    except ResponseError:
        return []


def get_destinations(amadeus: Client, origin_city_code: str) -> list[str]:
    try:
        resp = retry_call(lambda: amadeus.shopping.flight_destinations.get(origin=origin_city_code))
        arr = resp.data if isinstance(resp.data, list) else []
        # destination is usually a city IATA code
        return [d.get("destination") for d in arr if isinstance(d, dict) and d.get("destination")]
    except ResponseError:
        return []


def try_offers(amadeus: Client, origin_code: str, dest_code: str, date_str: str) -> list:
    resp = retry_call(
        lambda: amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_code,
            destinationLocationCode=dest_code,
            departureDate=date_str,
            adults=1,
        )
    )
    return resp.data if isinstance(resp.data, list) else []


def main():
    amadeus = env_credentials()
    today = datetime.utcnow().date()
    date_candidates = [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in (3, 7, 10, 14, 21, 28, 35, 42, 60, 75)]

    # Common city codes likely to have data
    city_codes = ["PAR", "LON", "MAD", "ROM", "MUC", "AMS", "FRA", "BCN", "ATH"]
    # Known airport pairs to probe directly
    airport_pairs = [
        ("CDG", "ATH"), ("CDG", "MAD"), ("CDG", "MUC"), ("CDG", "BCN"),
        ("LHR", "FRA"), ("FRA", "MUC"), ("AMS", "CDG"), ("MAD", "FRA"),
        ("BCN", "FCO"), ("ATH", "FRA"), ("FCO", "CDG"),
    ]

    # First, try direct airport pairs with many date candidates
    for (o_code, d_code) in airport_pairs:
        for date_str in date_candidates:
            try:
                data = try_offers(amadeus, o_code, d_code, date_str)
                if data:
                    price = None
                    try:
                        price = data[0].get("price", {}).get("total")
                    except Exception:
                        price = None
                    print(
                        f"FOUND origin={o_code} dest={d_code} used_origin={o_code} used_dest={d_code} date={date_str} count={len(data)} sample_price={price}"
                    )
                    return 0
            except ResponseError:
                continue

    # Next, iterate by city codes
    for origin in city_codes:
        dests = get_destinations(amadeus, origin)
        # prioritize top few destinations if available, else fallback to city list minus origin
        if not dests:
            dests = [c for c in city_codes if c != origin]
        dests = dests[:10]

        # compute airport variants for origin/dest when needed
        origin_airports = get_airports(amadeus, origin)
        for dest in dests:
            dest_airports = get_airports(amadeus, dest)
            attempts: list[tuple[str, str]] = [(origin, dest)]
            if origin_airports and dest_airports:
                attempts.append((origin_airports[0], dest_airports[0]))
            if origin_airports:
                attempts.append((origin_airports[0], dest))
            if dest_airports:
                attempts.append((origin, dest_airports[0]))

            for o_code, d_code in attempts:
                # Try provider-suggested dates first
                suggested_dates = []
                try:
                    resp_dates = retry_call(lambda: amadeus.shopping.flight_dates.get(origin=o_code, destination=d_code))
                    arr = resp_dates.data if isinstance(resp_dates.data, list) else []
                    for item in arr:
                        d = item.get("departureDate") or item.get("date")
                        if isinstance(d, str):
                            suggested_dates.append(d)
                except ResponseError:
                    pass
                try_order = suggested_dates + date_candidates
                for date_str in try_order[:15]:
                    try:
                        data = try_offers(amadeus, o_code, d_code, date_str)
                        if data:
                            price = None
                            try:
                                price = data[0].get("price", {}).get("total")
                            except Exception:
                                price = None
                            print(
                                f"FOUND origin={origin} dest={dest} used_origin={o_code} used_dest={d_code} date={date_str} count={len(data)} sample_price={price}"
                            )
                            return 0
                    except ResponseError:
                        continue

    print("No positive results found after exhaustive attempts.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
