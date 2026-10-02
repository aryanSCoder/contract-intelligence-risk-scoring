from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_dashboard():
    response = client.get("/")

    assert response.status_code == 200
    assert "Contract" in response.text


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_api_info():
    response = client.get("/api")

    assert response.status_code == 200

    data = response.json()

    assert "project" in data
    assert "endpoints" in data


def test_risk_report_endpoint():
    response = client.get("/risk-report")

    assert response.status_code == 200

    data = response.json()

    assert "risk_assessment" in data
    assert "risk_score" in data["risk_assessment"]
    assert "risk_level" in data["risk_assessment"]


def test_detected_clauses_endpoint():
    response = client.get("/detected-clauses")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)


def test_risk_details_endpoint():
    response = client.get("/risk-details")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)


def test_download_report_endpoint():
    response = client.get("/download-report")

    assert response.status_code == 200
    assert len(response.content) > 0


def test_semantic_search_success(monkeypatch):
    from app import main

    def fake_search(query, top_k=5):
        return [
            {
                "rank": 1,
                "score": 0.85,
                "section_id": "section_1",
                "title": "Confidentiality",
                "text": "The parties must protect confidential information.",
            }
        ]

    monkeypatch.setattr(main, "search", fake_search)

    response = client.post(
        "/search",
        json={
            "query": "confidentiality obligations",
            "top_k": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "confidentiality obligations"
    assert data["count"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Confidentiality"


def test_semantic_search_invalid_request():
    response = client.post(
        "/search",
        json={
            "query": "a",
            "top_k": 3
        }
    )

    assert response.status_code == 422


def test_semantic_search_invalid_top_k():
    response = client.post(
        "/search",
        json={
            "query": "termination",
            "top_k": 100
        }
    )

    assert response.status_code == 422