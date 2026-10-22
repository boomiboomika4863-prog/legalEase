from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["app"] == "LegalEase"

def test_generate_validates_required_fields():
    response = client.post("/generate", json={"document_type": "NDA"})
    assert response.status_code == 422
