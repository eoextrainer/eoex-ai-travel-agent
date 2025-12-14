from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import users, admin, journeys, amadeus_api

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

@app.get("/")
def root():
    return {"message": "EOEX AI Travel Agent API"}
