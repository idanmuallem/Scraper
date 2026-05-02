from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from routers.ingestion import router as ingestion_router
from routers.entities import router as entities_router
from services.scraper import fetch_financial_text
from services.ai_processor import AIProcessor
import db.models  # ensure model classes are registered with Base before create_all


def test_ingest_and_list_entities(monkeypatch):
    # Create fastapi app for testing
    app = FastAPI()
    app.include_router(ingestion_router)
    app.include_router(entities_router)

    # Setup in-memory sqlite
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Patch fetcher to return text
    async def _fake_fetch(url: str):
        return "E2E financial text"

    monkeypatch.setattr("routers.ingestion.fetch_financial_text", _fake_fetch)

    # Patch AIProcessor.extract to return a valid entity
    def fake_extract(self, text: str):
        return {"ticker": "MSFT", "sentiment": "Neutral", "insight": "Growth in cloud revenue"}

    monkeypatch.setattr(AIProcessor, "extract", fake_extract)

    client = TestClient(app)

    resp = client.post("/ingest", json={"source_url": "https://example.com/e2e"})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data and len(data["data"]) == 1

    # Verify entity is listed
    list_resp = client.get("/entities")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert isinstance(list_data, list) and len(list_data) == 1
    assert list_data[0]["ticker"] == "MSFT"
