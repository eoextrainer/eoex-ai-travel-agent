# Project Implementation

## Tech Stack
- Backend: FastAPI (Python), SQLAlchemy.
- DB: MySQL 8.
- Frontend: HTML/CSS/JS.
- Integration: Amadeus Python SDK.
- Tooling: Pytest, Flake8, Black, Docker.

## Local Setup
```bash
cd /media/eoex/DOJO/CONSULTING/PROJECTS/eoex-apps-travel-ai/eoex-ai-travel-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # fill AMADEUS credentials
```

## Run Backend
```bash
uvicorn backend.app.main:app --reload
```

## Initialize Database
```bash
export MYSQL_USER=eoex MYSQL_PASSWORD=eoex MYSQL_HOST=localhost MYSQL_DB=eoex_travel
bash backend/scripts/init_db.sh
```

## Docker
```bash
docker compose up --build
```

## Amadeus Test Code
```python
from amadeus import Client, ResponseError
amadeus = Client(client_id='REPLACE_BY_YOUR_API_KEY', client_secret='REPLACE_BY_YOUR_API_SECRET')
try:
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='MAD', destinationLocationCode='ATH', departureDate='2024-11-01', adults=1)
    print(response.data)
except ResponseError as error:
    print(error)
```

## Testing & Linting
```bash
pytest -q
flake8
black --check .
```

## Admin Dashboard API
- `GET /api/admin/dashboard?user=traveler-1&destination=ATH&budget=2000`

## Workflows Script
- Use `./app-changes.sh` to guide new dev, feature, and bugfix flows.
