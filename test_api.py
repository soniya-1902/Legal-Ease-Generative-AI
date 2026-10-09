import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["MOCK_AI"] = "true"

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "LegalEase API is running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate():
    response = client.post("/generate", json={
        "document_type": "Non-Disclosure Agreement",
        "parties": "Jane Doe (Disclosing Party), TechNova Inc. (Receiving Party)",
        "terms": "Protect confidential information; No unauthorized disclosure; 15 days notice",
        "effective_date": "September 30, 2026",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mock"] is True
    assert "NON-DISCLOSURE AGREEMENT" in data["content"]


def test_export_txt():
    response = client.post("/export/txt", json={"content": "Hello LegalEase", "document_type": "Test"})
    assert response.status_code == 200
    assert response.text == "Hello LegalEase"


def test_export_docx():
    response = client.post("/export/docx", json={"content": "TEST AGREEMENT\n\nA simple paragraph.", "document_type": "Test Agreement"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert response.content[:2] == b"PK"


def test_export_pdf():
    response = client.post("/export/pdf", json={"content": "TEST AGREEMENT\n\nA simple paragraph.", "document_type": "Test Agreement"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
