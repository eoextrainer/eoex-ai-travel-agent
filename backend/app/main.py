from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from .routes import users, admin, journeys, amadeus_api, geo
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(Path(__file__).resolve().parents[2], ".env"), override=False)
app = FastAPI(title="EOEX AI Travel Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(journeys.router, prefix="/api/journeys", tags=["journeys"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(amadeus_api.router, prefix="/api/amadeus", tags=["amadeus"])
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])

@app.get("/")
def root():
    return {"message": "EOEX AI Travel Agent API"}

# Serve frontend static files
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

@app.get("/index.html", response_class=HTMLResponse)
def index_html():
    try:
        return (frontend_dir / "index.html").read_text(encoding="utf-8")
    except Exception:
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)

# Auto-seed geography data on startup
@app.on_event("startup")
def seed_geography_on_startup():
    try:
        geo.seed_geo()
    except Exception:
        # Ignore errors during startup seeding to avoid blocking app
        pass
