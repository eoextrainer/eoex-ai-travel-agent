# eoex-ai-travel-agent

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AMADEUS_CLIENT_ID="<your_client_id>"
export AMADEUS_CLIENT_SECRET="<your_client_secret>"
uvicorn backend.app.main:app --reload --port 8000
```
Optional `.env` at repo root is supported and auto-loaded by the backend:

```bash
AMADEUS_CLIENT_ID=<your_client_id>
AMADEUS_CLIENT_SECRET=<your_client_secret>
MYSQL_USER=eoex
MYSQL_PASSWORD=eoex
MYSQL_HOST=127.0.0.1
MYSQL_DB=eoex_travel
CACHE_DEFAULT_TTL=600
```

## Serve Frontend
Visit `http://localhost:8000/index.html` to load the frontend via FastAPI static files.

## Geo Data Seeding & Verification

Seed and inspect continents, countries, and capitals:

```bash
curl -s -X POST http://127.0.0.1:8000/api/geo/seed
curl -s http://127.0.0.1:8000/api/geo/dump | jq '.counts,.continents,.countries[:10],.capitals[:10]'
```

On the homepage, a "Backend Data Snapshot" card will display a small preview fetched from `/api/geo/dump` to validate frontend-backend wiring.

## Codespaces
- Open the repo in GitHub Codespaces; `.devcontainer/devcontainer.json` will install dependencies.
- Run `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.

## Local Project Setup

- Virtualenv and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Environment variables: use `.env` at repo root

```bash
AMADEUS_CLIENT_ID=<your_client_id>
AMADEUS_CLIENT_SECRET=<your_client_secret>
MYSQL_USER=eoex
MYSQL_PASSWORD=eoex
MYSQL_HOST=127.0.0.1
MYSQL_DB=eoex_travel
CACHE_DEFAULT_TTL=600
```

- Start MySQL via Docker Compose and apply migrations

```bash
docker compose up -d db
bash backend/scripts/init_db.sh
```

- Start backend

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Docker Hub Publishing
1. Build image locally: `docker build -t eoex/eoex-ai-travel-agent:latest .`
2. Login: `docker login`
3. Tag: `docker tag eoex/eoex-ai-travel-agent:latest docker.io/eoex/eoex-ai-travel-agent:latest`
4. Push: `docker push docker.io/eoex/eoex-ai-travel-agent:latest`

Ensure the Docker Hub repository `eoex/eoex-ai-travel-agent` exists under your account.

## MySQL Setup
With Docker Compose (recommended):

```bash
docker compose up -d db
export MYSQL_USER=eoex MYSQL_PASSWORD=eoex MYSQL_HOST=127.0.0.1 MYSQL_DB=eoex_travel
bash backend/scripts/init_db.sh
```

System MySQL (if available):

```bash
sudo service mysql start
export MYSQL_USER=eoex MYSQL_PASSWORD=eoex MYSQL_HOST=localhost MYSQL_DB=eoex_travel
bash backend/scripts/init_db.sh
```

Note: On some distros, `mysql.service` may be masked; prefer Docker Compose.

## Tag and Release

```bash
git add -A
git commit -m "docs(setup): add compose/devcontainer setup; fix geo seeding; add dump endpoint; frontend wiring card"
git tag -a v0.2.0 -m "Geo wiring fix and Dockerized setup"
git push --follow-tags
```

## Amadeus API Test
Run a quick test against Amadeus once env vars are set:

```bash
python - <<'PY'
from amadeus import Client, ResponseError
import os
amadeus = Client(
	client_id=os.getenv('AMADEUS_CLIENT_ID'),
	client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)
try:
	resp = amadeus.shopping.flight_offers_search.get(
		originLocationCode='MAD',
		destinationLocationCode='ATH',
		departureDate='2024-11-01',
		adults=1)
	print(type(resp.data), len(resp.data))
except ResponseError as e:
	print(e)
PY
```

## API Response Shapes

- List-type endpoints return plain arrays for consistency:
	- `GET /api/journeys` → `[{...}, {...}]`
	- `GET /api/admin/dashboard` → `[{...}, {...}]`
	- Amadeus list endpoints already return arrays.


## Warm Cache and Seed Data

```bash
curl -s "http://127.0.0.1:8000/api/amadeus/locations?keyword=Athens&subType=CITY" >/dev/null
curl -s "http://127.0.0.1:8000/api/amadeus/hotel-offers?hotelIds=ADPAR001&adults=2" >/dev/null
curl -s "http://127.0.0.1:8000/api/amadeus/activities-by-geo?latitude=37.9838&longitude=23.7275" >/dev/null

curl -s -X POST "http://127.0.0.1:8000/api/amadeus/seed-from-flight-offers?origin=MAD&destination=ATH&departure=2026-01-15&adults=1&user_id=1&budget=2000.0"

curl -s -X POST http://127.0.0.1:8000/api/journeys/seed -H 'Content-Type: application/json' -d '{"user_id":1,"destination_country":"Greece","destination_city":"Athens","budget":2000.0,"flights":[{"airline":"BA","origin_city":"MAD","destination_city":"ATH","departure_date":"2026-01-15","arrival_date":"2026-01-15","price":250.00}],"accommodations":[{"name":"Hotel Athens","address":"1 Main St","city":"Athens","price_per_night":120.00}]}'
```

## Verify Data

```bash
curl -s http://127.0.0.1:8000/api/journeys | jq
curl -s "http://127.0.0.1:8000/api/admin/dashboard?user=traveler-1&destination=Athens&budget=2500" | jq
```

