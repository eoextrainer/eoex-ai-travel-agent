import os
import logging
from fastapi import APIRouter, HTTPException
from amadeus import Client, ResponseError

router = APIRouter()

logger = logging.getLogger("amadeus_logger")
logger.setLevel(logging.DEBUG)

def get_client():
    client_id = os.getenv("AMADEUS_CLIENT_ID", "")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Amadeus credentials not configured")
    return Client(client_id=client_id, client_secret=client_secret, logger=logger)

@router.get("/test")
def test_api():
    amadeus = get_client()
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode="MAD",
            destinationLocationCode="ATH",
            departureDate="2024-11-01",
            adults=1,
        )
        return response.data
    except ResponseError as error:
        raise HTTPException(status_code=500, detail=str(error))
