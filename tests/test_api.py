from fastapi.testclient import TestClient

from backend.main import app
from backend.utils.document_formatter import format_docx, format_pdf, format_txt

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "LegalEase API"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_validation():
    response = client.post("/generate", json={})
    assert response.status_code == 422


def test_formatters():
    sample = """NON-DISCLOSURE AGREEMENT

1. Confidentiality

The receiving party shall protect
confidential information.

2. Term

The agreement begins on
October 1, 2026.
"""

    txt = format_txt(sample)
    assert b"NON-DISCLOSURE" in txt

    docx = format_docx(sample, "Non-Disclosure Agreement")
    assert len(docx) > 1000

    pdf = format_pdf(sample, "Non-Disclosure Agreement")
    assert pdf.startswith(b"%PDF")