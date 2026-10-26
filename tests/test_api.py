from fastapi.testclient import TestClient
import os
from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Document AI Backend is running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_process_id_no_file():
    response = client.post("/api/v1/process-id")
    assert response.status_code == 422


def test_process_id_invalid_file_type():
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = client.post("/api/v1/process-id", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_get_nonexistent_record():
    response = client.get("/api/v1/records/non-existent-id-12345")
    assert response.status_code == 404
    assert response.json()["detail"] == "Record not found"