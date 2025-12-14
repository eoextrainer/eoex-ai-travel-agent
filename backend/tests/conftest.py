import os
import sys
import pathlib
import pytest
from sqlalchemy import text

# Ensure repo root is on sys.path so `backend.app` can be imported when running pytest from root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.db import engine
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="session", autouse=True)
def bootstrap_db():
    os.environ.setdefault("MYSQL_USER", "eoex")
    os.environ.setdefault("MYSQL_PASSWORD", "eoex")
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_DB", "eoex_travel")

    migration_path = pathlib.Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
    sql = migration_path.read_text()
    # Apply migration if tables aren't present; safe to run due to IF NOT EXISTS in SQL
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(stmt))
    yield


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
