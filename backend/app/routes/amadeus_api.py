import os
import logging
from fastapi import APIRouter, HTTPException, Query
from amadeus import Client, ResponseError
import time
from ..db import engine
from ..utils.cache import get_cache, set_cache
from sqlalchemy import text

router = APIRouter()

logger = logging.getLogger("amadeus_logger")
logger.setLevel(logging.DEBUG)

def get_client():
    client_id = os.getenv("AMADEUS_CLIENT_ID", "")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "")
    host_env = os.getenv("AMADEUS_HOST", "test").lower()
    host_param = None
    if host_env in ("production", "prod"):
        host_param = 'production'
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Amadeus credentials not configured")
    if host_param:
        return Client(client_id=client_id, client_secret=client_secret, logger=logger, host=host_param)
    return Client(client_id=client_id, client_secret=client_secret, logger=logger)

# Default origin airport handling (prefer verified CDG)
DEFAULT_ORIGIN_IATA = None

def get_default_origin_iata():
    global DEFAULT_ORIGIN_IATA
    if DEFAULT_ORIGIN_IATA:
        return DEFAULT_ORIGIN_IATA
    cached = get_cache("default_origin_iata", ttl=86400)
    if cached:
        DEFAULT_ORIGIN_IATA = cached
        return DEFAULT_ORIGIN_IATA
    amadeus = get_client()
    iata = None
    try:
        resp = amadeus.reference_data.locations.get(keyword="CDG", subType="AIRPORT")
        data = resp.data if isinstance(resp.data, list) else []
        for item in data:
            code = item.get("iataCode") or (item.get("address") or {}).get("iataCode")
            if code == "CDG":
                iata = "CDG"
                break
    except ResponseError:
        iata = None
    DEFAULT_ORIGIN_IATA = iata or "CDG"
    set_cache("default_origin_iata", DEFAULT_ORIGIN_IATA)
    return DEFAULT_ORIGIN_IATA

def _raise_http_error(error: ResponseError):
    detail = getattr(error, 'response', None)
    corr = None
    if detail:
        headers = getattr(detail, 'headers', {}) or {}
        corr = headers.get('X-CorrelationID') or headers.get('x-correlation-id')
    body = None
    if detail and hasattr(detail, 'body'):
        body = detail.body
    message = body or str(error)
    if corr:
        message = f"{message} [correlation_id={corr}]"
    raise HTTPException(status_code=500, detail=message)

def retry_call(fn, max_retries: int = 3, backoff_sec: float = 0.8):
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn()
        except ResponseError as err:
            last_err = err
            resp = getattr(err, 'response', None)
            status = getattr(resp, 'status_code', None)
            if status and int(status) >= 500 and attempt < max_retries - 1:
                time.sleep(backoff_sec * (2 ** attempt))
                continue
            break
    _raise_http_error(last_err)

@router.get("/health")
def health():
    try:
        _ = get_client()
        return {"status": "ok", "credentials": True}
    except HTTPException as e:
        return {"status": "error", "credentials": False, "detail": e.detail}

@router.get("/test")
def test_api(
    origin: str = Query("CDG"),
    destination: str = Query("ATH"),
    departure: str = Query("2026-01-15"),
    adults: int = Query(1),
):
    amadeus = get_client()
    cache_key = f"flight_offers_search_{origin}_{destination}_{departure}_{adults}"
    cached = get_cache(cache_key, ttl=600)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure,
            adults=adults,
        )
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data

@router.get("/checkin-links")
def checkin_links(airlineCode: str = Query("BA")):
    amadeus = get_client()
    cache_key = f"checkin_links_{airlineCode}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.reference_data.urls.checkin_links.get(airlineCode=airlineCode)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data

@router.get("/locations")
def locations(keyword: str = Query("Athens"), subType: str = Query("CITY")):
    amadeus = get_client()
    cache_key = f"locations_{keyword}_{subType}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.get('/v1/reference-data/locations', keyword=keyword, subType=subType)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/flight-destinations")
def flight_destinations(origin: str = Query("CDG")):
    amadeus = get_client()
    cache_key = f"flight_destinations_{origin}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.flight_destinations.get(origin=origin)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/flight-dates")
def flight_dates(origin: str = Query("CDG"), destination: str = Query("MUC")):
    amadeus = get_client()
    cache_key = f"flight_dates_{origin}_{destination}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.flight_dates.get(origin=origin, destination=destination)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/hotel-offers")
def hotel_offers(hotelIds: str = Query("ADPAR001"), adults: int = Query(2)):
    amadeus = get_client()
    cache_key = f"hotel_offers_{hotelIds}_{adults}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.hotel_offers_search.get(hotelIds=hotelIds, adults=str(adults))
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.post("/seed-from-flight-offers")
def seed_from_flight_offers(
    origin: str = Query("CDG"),
    destination: str = Query("ATH"),
    departure: str = Query("2026-01-15"),
    adults: int = Query(1),
    user_id: int = Query(1),
    budget: float = Query(2000.0),
):
    amadeus = get_client()
    def do_get():
        return amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure,
            adults=adults,
        )
    response = retry_call(do_get)
    offers = response.data if isinstance(response.data, list) else []
    with engine.begin() as conn:
        res = conn.execute(text(
            "INSERT INTO journeys (user_id, destination_country, destination_city, budget) VALUES (:user_id, :destination_country, :destination_city, :budget)"
        ), {
            "user_id": user_id,
            "destination_country": destination,
            "destination_city": destination,
            "budget": budget
        })
        journey_id = res.lastrowid
        for off in offers[:10]:
            price = None
            try:
                price = float(off.get('price', {}).get('total'))
            except Exception:
                price = None
            segments = (off.get('itineraries', [{}])[0].get('segments', []) if off else [])
            origin_city = segments[0]['departure']['iataCode'] if segments else origin
            dest_city = segments[-1]['arrival']['iataCode'] if segments else destination
            conn.execute(text(
                "INSERT INTO flights (journey_id, airline, origin_city, destination_city, departure_date, arrival_date, price) VALUES (:journey_id, :airline, :origin_city, :destination_city, :departure_date, :arrival_date, :price)"
            ), {
                "journey_id": journey_id,
                "airline": (segments[0].get('carrierCode') if segments else None),
                "origin_city": origin_city,
                "destination_city": dest_city,
                "departure_date": departure,
                "arrival_date": departure,
                "price": price
            })
        # Seed hotel offers if a warmed cache exists (robust parsing)
        try:
            # Attempt known warmed key example (ADPAR001 for Athens), else skip silently
            possible_keys = [
                f"hotel_offers_ADPAR001_{adults}",
                f"hotel_offers_{destination}_{adults}",
            ]
            hotel_data = None
            for k in possible_keys:
                hotel_data = get_cache(k)
                if hotel_data:
                    break
            for h in (hotel_data or [])[:5]:
                name = (h.get('hotel', {}) or {}).get('name')
                address_lines = ((h.get('hotel', {}) or {}).get('address', {}) or {}).get('lines', [])
                address = address_lines[0] if address_lines else None
                offers = h.get('offers') or []
                price = None
                if offers:
                    try:
                        price = float((offers[0].get('price') or {}).get('total'))
                    except Exception:
                        price = None
                conn.execute(text(
                    "INSERT INTO accommodations (journey_id, name, address, city, price_per_night) VALUES (:journey_id, :name, :address, :city, :price_per_night)"
                ), {
                    "journey_id": journey_id,
                    "name": name,
                    "address": address,
                    "city": destination,
                    "price_per_night": price,
                })
        except Exception:
            pass

        # Seed activities using city geocode if available; prefer warmed cache, else fetch live
        try:
            lat = None
            lon = None
            try:
                loc_resp = retry_call(lambda: amadeus.get('/v1/reference-data/locations', keyword=destination, subType='CITY'))
                locs = loc_resp.data if isinstance(loc_resp.data, list) else []
                if locs:
                    geo = (locs[0].get('geoCode') or {})
                    lat = geo.get('latitude')
                    lon = geo.get('longitude')
            except Exception:
                pass
            acts_data = []
            if lat is not None and lon is not None:
                cache_key = f"activities_geo_{lat}_{lon}"
                acts_data = get_cache(cache_key) or []
                if not acts_data:
                    try:
                        acts_resp = retry_call(lambda: amadeus.shopping.activities.get(latitude=lat, longitude=lon))
                        acts_data = acts_resp.data
                        set_cache(cache_key, acts_data)
                    except Exception:
                        acts_data = []
            for a in acts_data[:5]:
                conn.execute(text(
                    "INSERT INTO places_to_visit (journey_id, place_name, category, description) VALUES (:journey_id, :place_name, :category, :description)"
                ), {
                    "journey_id": journey_id,
                    "place_name": a.get('name'),
                    "category": a.get('type'),
                    "description": a.get('shortDescription')
                })
        except Exception:
            pass
    return {"journey_id": journey_id, "flights_seeded": min(len(offers), 10)}

# Additional endpoints
@router.get("/airlines")
def airlines(airlineCodes: str = Query("BA")):
    amadeus = get_client()
    def do_get():
        return amadeus.reference_data.airlines.get(airlineCodes=airlineCodes)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/locations-any")
def locations_any(keyword: str = Query("LON")):
    amadeus = get_client()
    def do_get():
        return amadeus.reference_data.locations.get(keyword=keyword, subType="ANY")
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/locations-city")
def locations_city(keyword: str = Query("PAR")):
    amadeus = get_client()
    def do_get():
        return amadeus.reference_data.locations.cities.get(keyword=keyword)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/locations-airports")
def locations_airports(longitude: float = Query(0.1278), latitude: float = Query(51.5074)):
    amadeus = get_client()
    def do_get():
        return amadeus.reference_data.locations.airports.get(longitude=longitude, latitude=latitude)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/air-traffic-booked")
def air_traffic_booked(originCityCode: str = Query("MAD"), period: str = Query("2017-08")):
    amadeus = get_client()
    def do_get():
        return amadeus.travel.analytics.air_traffic.booked.get(originCityCode=originCityCode, period=period)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/air-traffic-traveled")
def air_traffic_traveled(originCityCode: str = Query("MAD"), period: str = Query("2017-01")):
    amadeus = get_client()
    def do_get():
        return amadeus.travel.analytics.air_traffic.traveled.get(originCityCode=originCityCode, period=period)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/air-traffic-busiest")
def air_traffic_busiest(cityCode: str = Query("MAD"), period: str = Query("2017"), direction: str = Query("ARRIVING")):
    amadeus = get_client()
    def do_get():
        return amadeus.travel.analytics.air_traffic.busiest_period.get(cityCode=cityCode, period=period, direction=direction)
    response = retry_call(do_get)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/activities-by-geo")
def activities_by_geo(latitude: float = Query(40.41436995), longitude: float = Query(-3.69170868)):
    amadeus = get_client()
    cache_key = f"activities_geo_{latitude}_{longitude}"
    cached = get_cache(cache_key, ttl=900)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.activities.get(latitude=latitude, longitude=longitude)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/activities-by-square")
def activities_by_square(north: float = Query(41.397158), west: float = Query(2.160873), south: float = Query(41.394582), east: float = Query(2.177181)):
    amadeus = get_client()
    cache_key = f"activities_square_{north}_{west}_{south}_{east}"
    cached = get_cache(cache_key, ttl=900)
    if cached is not None:
        return cached
    def do_get():
        return amadeus.shopping.activities.by_square.get(north=north, west=west, south=south, east=east)
    response = retry_call(do_get)
    set_cache(cache_key, response.data)
    return response.data if isinstance(response.data, list) else [response.data]

@router.get("/flight-offers-by-cities")
def flight_offers_by_cities(
    originCity: str = Query("Paris"),
    destinationCity: str = Query("Athens"),
    departure: str = Query("2026-01-15"),
    adults: int = Query(1),
    includeMeta: bool = Query(False),
):
    amadeus = get_client()
    # Resolve IATA codes from city names: prefer CITY code, also gather AIRPORT codes for fallback
    def resolve_codes(city_name: str):
        city_code = None
        airport_codes = []
        try:
            resp_city = amadeus.reference_data.locations.cities.get(keyword=city_name)
            data_city = resp_city.data if isinstance(resp_city.data, list) else []
            if data_city:
                city_code = data_city[0].get('iataCode')
        except ResponseError:
            pass
        try:
            resp_air = amadeus.reference_data.locations.get(keyword=city_name, subType="AIRPORT")
            data_air = resp_air.data if isinstance(resp_air.data, list) else []
            for item in data_air:
                code = item.get('iataCode') or (item.get('address') or {}).get('iataCode')
                if code:
                    airport_codes.append(code)
        except ResponseError:
            pass
        return city_code, airport_codes

    def try_offers(o_code: str, d_code: str, date_str: str):
        def do_get():
            return amadeus.shopping.flight_offers_search.get(
                originLocationCode=o_code,
                destinationLocationCode=d_code,
                departureDate=date_str,
                adults=adults,
            )
        try:
            resp = retry_call(do_get, max_retries=2, backoff_sec=0.6)
            return resp.data if isinstance(resp.data, list) else []
        except HTTPException:
            return []

    def suggested_dates(o_code: str, d_code: str):
        try:
            resp = retry_call(lambda: amadeus.shopping.flight_dates.get(origin=o_code, destination=d_code), max_retries=2, backoff_sec=0.6)
            arr = resp.data if isinstance(resp.data, list) else []
            out = []
            for item in arr:
                d = item.get('departureDate') or item.get('date')
                if isinstance(d, str):
                    out.append(d)
            return out
        except HTTPException:
            return []

    origin_city_code, origin_airports = resolve_codes(originCity)
    dest_city_code, dest_airports = resolve_codes(destinationCity)

    # Build attempt pairs: city→city, airport→airport (first), airport combos
    attempts = []
    if origin_city_code and dest_city_code:
        attempts.append((origin_city_code, dest_city_code))
    if origin_airports and dest_airports:
        attempts.append((origin_airports[0], dest_airports[0]))
    if origin_city_code and dest_airports:
        attempts.append((origin_city_code, dest_airports[0]))
    if origin_airports and dest_city_code:
        attempts.append((origin_airports[0], dest_city_code))

    # First try requested date
    for o_code, d_code in attempts:
        data = try_offers(o_code, d_code, departure)
        if data:
            return ({"data": data, "meta": {"origin": o_code, "dest": d_code, "date": departure, "fallback": False}} if includeMeta else data)

    # Fallback to suggested dates near requested
    for o_code, d_code in attempts:
        dates = suggested_dates(o_code, d_code)
        if not dates:
            continue
        # sort by proximity to requested
        try:
            from datetime import datetime
            req_dt = datetime.strptime(departure, "%Y-%m-%d")
            dates = sorted(dates, key=lambda s: abs((datetime.strptime(s, "%Y-%m-%d") - req_dt).days))
        except Exception:
            pass
        for d in dates[:3]:
            data = try_offers(o_code, d_code, d)
            if data:
                return ({"data": data, "meta": {"origin": o_code, "dest": d_code, "date": d, "fallback": True}} if includeMeta else data)

    # If all attempts failed or returned empty, surface empty list for UX
    return ({"data": [], "meta": {"origin": attempts[0][0] if attempts else None, "dest": attempts[0][1] if attempts else None, "date": departure, "fallback": True}} if includeMeta else [])
