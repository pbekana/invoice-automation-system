import pytest
from unittest.mock import patch, MagicMock

def test_get_invoices_mocked(client, mock_db_manager):
    mock_db_manager.get_all_invoices.return_value = [{"_id": "1", "company": "Test", "total": 100.0}]
    response = client.get("/invoices")
    assert response.status_code == 200
    assert response.json[0]["company"] == "Test"

def test_dashboard_mocked(client, mock_db_manager):
    mock_db_manager.get_dashboard_summary.return_value = {"grand_total": 500.0, "total_invoices": 5}
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json["grand_total"] == 500.0

def test_chat_stats_mocked(client, mock_db_manager):
    mock_db_manager.get_dashboard_summary.return_value = {"grand_total": 120.50, "total_invoices": 3}
    response = client.post("/chat", json={"message": "total spending"})
    assert response.status_code == 200
    assert "120.50" in response.json["response"]

def test_upload_no_file(client):
    response = client.post("/upload")
    assert response.status_code == 400
    assert "No file" in response.json["error"]
