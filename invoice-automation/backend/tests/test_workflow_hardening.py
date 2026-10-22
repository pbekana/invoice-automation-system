"""
End-to-End tests for Workflow Hardening, User Roles (RBAC),
Revision Request, Reconciliation, and Exports.
"""

import pytest
import io
import csv
from datetime import datetime, timedelta
from bson import ObjectId
from models.invoice import Invoice, InvoiceStatus
from models.user import UserRole
from utils.money import to_decimal, to_float
from db import db_manager
from services.reconciliation_service import ReconciliationService


def _get_token_for(client, email, name, role):
    client.post("/api/auth/register", json={
        "email": email, "name": name, "password": "Password123!", "roles": [role]
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json["access_token"], resp.json["user"]["id"]


def test_viewer_role_prohibitions(client):
    """Verify that Viewer cannot upload, submit, approve, edit, or record payments."""
    viewer_email = f"viewer_{ObjectId()}@example.com"
    viewer_token, viewer_id = _get_token_for(client, viewer_email, "Audit Viewer", UserRole.VIEWER)
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # 1. Viewer attempts to upload bill -> 403 Forbidden
    data = {"file": (io.BytesIO(b"%PDF-1.4\nfake pdf"), "bill.pdf")}
    up_resp = client.post("/upload", data=data, content_type="multipart/form-data", headers=viewer_headers)
    assert up_resp.status_code == 403
    assert "Insufficient permissions" in up_resp.json.get("error", "")

    # 2. Create a draft invoice directly in DB
    inv_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv_id),
        "company": "Vendor Test",
        "total": 150.00,
        "status": "draft",
        "currency": "USD"
    })

    # 3. Viewer attempts to submit invoice -> 403 Forbidden
    sub_resp = client.post(f"/api/invoices/{inv_id}/submit", headers=viewer_headers)
    assert sub_resp.status_code == 403

    # 4. Viewer attempts to edit invoice -> 403 Forbidden
    edit_resp = client.patch(f"/api/invoices/{inv_id}", json={"total": 200.00}, headers=viewer_headers)
    assert edit_resp.status_code == 403

    # 5. Viewer attempts to approve invoice -> 403 Forbidden
    app_resp = client.post(f"/api/invoices/{inv_id}/approve", json={"comments": "ok"}, headers=viewer_headers)
    assert app_resp.status_code == 403

    # 6. Viewer attempts to record payment -> 403 Forbidden
    pay_resp = client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 150.00}, headers=viewer_headers)
    assert pay_resp.status_code == 403


def test_revision_and_resubmission_lifecycle(client):
    """Test full cycle: Submit -> Approver requests revision -> Submitter edits -> Resubmit -> Approve."""
    sub_email = f"sub_{ObjectId()}@example.com"
    sub_token, sub_id = _get_token_for(client, sub_email, "Submitter User", UserRole.SUBMITTER)
    sub_headers = {"Authorization": f"Bearer {sub_token}"}

    app_email = f"app_{ObjectId()}@example.com"
    app_token, app_id = _get_token_for(client, app_email, "Approver User", UserRole.APPROVER)
    app_headers = {"Authorization": f"Bearer {app_token}"}

    # Submitter creates invoice in DB as draft
    inv_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv_id),
        "company": "Stationery Co",
        "total": 80.00,
        "submitter_id": sub_id,
        "status": "draft",
        "category": "Supplies",
        "approval_chain": []
    })

    # Submitter submits invoice
    sub_resp = client.post(f"/api/invoices/{inv_id}/submit", headers=sub_headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json["invoice"]["status"] == "pending_approval"

    # Approver requests revision with feedback
    rev_resp = client.post(
        f"/api/invoices/{inv_id}/request-revision",
        json={"reason": "Missing receipt attachment and item description"},
        headers=app_headers
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json["invoice"]["status"] == "needs_revision"

    # Submitter edits invoice to fix issues
    patch_resp = client.patch(
        f"/api/invoices/{inv_id}",
        json={"notes": "Attached detailed receipt items"},
        headers=sub_headers
    )
    assert patch_resp.status_code == 200

    # Submitter resubmits invoice
    resub_resp = client.post(f"/api/invoices/{inv_id}/submit", headers=sub_headers)
    assert resub_resp.status_code == 200
    assert resub_resp.json["invoice"]["status"] == "pending_approval"

    # Approver approves invoice
    final_app = client.post(f"/api/invoices/{inv_id}/approve", json={"comments": "Looks good now"}, headers=app_headers)
    assert final_app.status_code == 200
    assert final_app.json["invoice"]["status"] == "approved"


def test_dynamic_overdue_calculation():
    """Verify that is_overdue dynamically calculates from due date and outstanding balance."""
    past_date = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
    inv1 = Invoice(
        company="Vendor Past Due",
        date="2026-09-01",
        total=100.00,
        category="General",
        submitter_id=str(ObjectId()),
        status=InvoiceStatus.APPROVED,
        due_date=past_date,
        outstanding_balance=100.00
    )
    assert inv1.is_overdue is True
    assert inv1.to_json()["is_overdue"] is True

    inv2 = Invoice(
        company="Vendor Paid",
        date="2026-09-01",
        total=100.00,
        category="General",
        submitter_id=str(ObjectId()),
        status=InvoiceStatus.PAID,
        due_date=past_date,
        outstanding_balance=0.00
    )
    assert inv2.is_overdue is False

    future_date = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d")
    inv3 = Invoice(
        company="Vendor Future",
        date="2026-10-01",
        total=100.00,
        category="General",
        submitter_id=str(ObjectId()),
        status=InvoiceStatus.APPROVED,
        due_date=future_date,
        outstanding_balance=100.00
    )
    assert inv3.is_overdue is False


def test_bank_statement_reconciliation(mongo_db):
    """Test importing bank statement CSV, matching against payments, and duplicate prevention."""
    rec_service = ReconciliationService(mongo_db)
    user_id = str(ObjectId())

    # Create recorded payment in payments collection
    p1_id = str(ObjectId())
    mongo_db["payments"].insert_one({
        "_id": ObjectId(p1_id),
        "invoice_id": str(ObjectId()),
        "amount": 250.00,
        "payment_date": "2026-10-15",
        "created_by": user_id,
        "status": "completed",
        "transaction_reference": "WIRE-9921",
        "payment_method": "bank_transfer"
    })

    # Prepare bank statement CSV
    statement_csv = (
        "Date,Description,Amount\n"
        "2026-10-15,Payment to Vendor WIRE-9921,250.00\n"
        "2026-10-16,Unrecorded Office Supplies,45.50\n"
    )

    # First import -> Should match 1, unmatch 1
    succ, result, err = rec_service.import_and_reconcile_statement(statement_csv, user_id, "oct_statement.csv")
    assert succ is True
    assert result["total_count"] == 2
    assert result["matched_count"] == 1
    assert result["unmatched_count"] == 1
    assert result["items"][0]["status"] == "matched"
    assert result["items"][0]["matched_payment_id"] == p1_id
    assert result["items"][1]["status"] == "unmatched"

    # Duplicate import -> Must be rejected
    succ2, res2, err2 = rec_service.import_and_reconcile_statement(statement_csv, user_id, "oct_statement.csv")
    assert succ2 is False
    assert "Duplicate statement import" in err2


def test_csv_exports(client):
    """Verify that vendor, customer, and payment CSV export endpoints return valid CSVs."""
    admin_email = f"admin_{ObjectId()}@example.com"
    token, admin_id = _get_token_for(client, admin_email, "Admin Export", UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}

    # Add sample vendor, customer, payment
    db_manager.db["vendors"].insert_one({
        "name": "ACME Supplies", "email": "acme@example.com", "phone": "555-1234",
        "status": "active", "created_at": datetime.utcnow()
    })
    db_manager.db["customers"].insert_one({
        "name": "Globex Corp", "email": "billing@globex.com", "phone": "555-9876",
        "currency": "USD", "payment_terms": "Net 30"
    })
    db_manager.db["payments"].insert_one({
        "invoice_id": str(ObjectId()), "amount": 120.00, "currency": "USD",
        "payment_date": "2026-10-10", "payment_method": "check",
        "transaction_reference": "CHK-1001", "status": "completed", "created_at": datetime.utcnow()
    })

    # Test vendor export
    v_resp = client.get("/api/export/vendors", headers=headers)
    assert v_resp.status_code == 200
    assert "ACME Supplies" in v_resp.text
    assert "Name,Email,Phone" in v_resp.text

    # Test customer export
    c_resp = client.get("/api/export/customers", headers=headers)
    assert c_resp.status_code == 200
    assert "Globex Corp" in c_resp.text
    assert "Billing Address" in c_resp.text

    # Test payment export
    p_resp = client.get("/api/export/payments", headers=headers)
    assert p_resp.status_code == 200
    assert "CHK-1001" in p_resp.text
    assert "Payment ID,Invoice ID,Amount" in p_resp.text
