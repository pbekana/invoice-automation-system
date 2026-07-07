import pytest
from unittest.mock import patch, MagicMock

def test_get_invoices_mocked(client, auth_headers, monkeypatch):
    from services.invoice_service import InvoiceService
    from models.invoice import Invoice
    
    mock_invoice = Invoice(
        _id="1",
        company="Test",
        date="2026-07-01",
        total=100.0,
        category="Supplies",
        submitter_id="test_user_id"
    )
    monkeypatch.setattr(InvoiceService, "list_invoices", lambda *args, **kwargs: [mock_invoice])
    
    response = client.get("/invoices", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["invoices"][0]["company"] == "Test"

def test_dashboard_mocked(client, auth_headers, monkeypatch):
    from db import DatabaseManager
    monkeypatch.setattr(DatabaseManager, "get_dashboard_summary", lambda self: {"grand_total": 500.0, "total_invoices": 5, "categories": {}})
    
    response = client.get("/dashboard", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["grand_total"] == 500.0

def test_chat_stats_mocked(client, auth_headers, monkeypatch):
    from db import DatabaseManager
    monkeypatch.setattr(DatabaseManager, "get_dashboard_summary", lambda self: {"grand_total": 120.50, "total_invoices": 3, "categories": {}})
    
    response = client.post("/chat", json={"message": "total spending"}, headers=auth_headers)
    assert response.status_code == 200
    assert "120.50" in response.json["response"]

def test_upload_no_file(client, auth_headers):
    response = client.post("/upload", headers=auth_headers)
    assert response.status_code == 400
    assert "No file" in response.json["error"]

