"""
Comprehensive tests for Role-Based Invoice Status Control,
Segregation of Duties, Terminal States, and Audit Trail Persistence & Immutability.
"""

import io
from datetime import datetime
from bson import ObjectId
import pytest

from models.invoice import Invoice, InvoiceStatus
from models.user import UserRole, User
from db import db_manager


def _get_token_for(client, email, name, role):
    client.post("/api/auth/register", json={
        "email": email, "name": name, "password": "Password123!", "roles": [role]
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json["access_token"], resp.json["user"]["id"]


def test_user_role_finance_model():
    """Verify UserRole.FINANCE enum and helper methods on User model."""
    assert UserRole.FINANCE == "finance"
    assert UserRole.is_valid_role("finance")
    assert UserRole.is_valid_role("finance_user")

    finance_user = User(email="fin@example.com", name="Fin User", roles=[UserRole.FINANCE])
    assert finance_user.is_finance() is True
    assert finance_user.can_pay() is True
    assert finance_user.can_approve() is False

    approver_user = User(email="app@example.com", name="App User", roles=[UserRole.APPROVER])
    assert approver_user.is_finance() is False
    assert approver_user.can_pay() is False
    assert approver_user.can_approve() is True


def test_submitter_permissions_and_segregation_of_duties(client):
    """
    Verify Submitter:
    - Can submit their own invoice
    - Can cancel their own submitted invoice
    - Cannot approve or reject invoices (including their own - segregation of duties)
    - Cannot mark invoices as paid
    - Cannot cancel another user's invoice
    """
    sub1_token, sub1_id = _get_token_for(client, f"sub1_{ObjectId()}@example.com", "Submitter 1", UserRole.SUBMITTER)
    sub2_token, sub2_id = _get_token_for(client, f"sub2_{ObjectId()}@example.com", "Submitter 2", UserRole.SUBMITTER)
    h_sub1 = {"Authorization": f"Bearer {sub1_token}"}
    h_sub2 = {"Authorization": f"Bearer {sub2_token}"}

    # Create invoice submitted by sub1
    inv1_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv1_id),
        "company": "Vendor Alpha",
        "total": 350.00,
        "submitter_id": sub1_id,
        "status": InvoiceStatus.SUBMITTED,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "status_history": [{
            "invoice_id": inv1_id,
            "previous_status": "draft",
            "new_status": InvoiceStatus.SUBMITTED,
            "user_id": sub1_id,
            "role": "submitter",
            "timestamp": datetime.utcnow(),
            "reason": "Initial submission"
        }]
    })

    # Submitter cannot approve their own invoice (segregation of duties)
    res_app = client.post(f"/api/invoices/{inv1_id}/approve", json={"comments": "I approve my own invoice"}, headers=h_sub1)
    assert res_app.status_code == 403

    # Submitter cannot reject an invoice
    res_rej = client.post(f"/api/invoices/{inv1_id}/reject", json={"reason": "Rejecting"}, headers=h_sub1)
    assert res_rej.status_code == 403

    # Submitter cannot mark an invoice as paid
    res_paid = client.post(f"/api/invoices/{inv1_id}/paid", json={}, headers=h_sub1)
    assert res_paid.status_code == 403

    # Submitter 2 cannot cancel Submitter 1's invoice
    res_cancel_sub2 = client.post(f"/api/invoices/{inv1_id}/cancel", json={"reason": "Cancel other's invoice"}, headers=h_sub2)
    assert res_cancel_sub2.status_code == 403

    # Submitter 1 can cancel their own submitted invoice
    res_cancel_sub1 = client.post(f"/api/invoices/{inv1_id}/cancel", json={"reason": "Duplicate submission"}, headers=h_sub1)
    assert res_cancel_sub1.status_code == 200
    assert res_cancel_sub1.json["invoice"]["status"] == InvoiceStatus.CANCELLED

    # Verify history was recorded for the cancellation
    doc = db_manager.db["invoices"].find_one({"_id": ObjectId(inv1_id)})
    assert doc["status"] == InvoiceStatus.CANCELLED
    assert len(doc["status_history"]) == 2
    latest_hist = doc["status_history"][-1]
    assert latest_hist["previous_status"] == InvoiceStatus.SUBMITTED
    assert latest_hist["new_status"] == InvoiceStatus.CANCELLED
    assert latest_hist["user_id"] == sub1_id
    assert "Duplicate submission" in latest_hist["reason"]


def test_approver_and_finance_separation(client):
    """
    Verify Approver:
    - Can approve/reject submitted invoices
    - Cannot mark invoices as paid
    Verify Finance User:
    - Can mark approved invoices as paid
    - Cannot mark unapproved invoices as paid
    - Cannot approve or reject invoices
    """
    sub_token, sub_id = _get_token_for(client, f"sub_{ObjectId()}@example.com", "Submitter A", UserRole.SUBMITTER)
    app_token, app_id = _get_token_for(client, f"app_{ObjectId()}@example.com", "Approver B", UserRole.APPROVER)
    fin_token, fin_id = _get_token_for(client, f"fin_{ObjectId()}@example.com", "Finance C", UserRole.FINANCE)

    h_sub = {"Authorization": f"Bearer {sub_token}"}
    h_app = {"Authorization": f"Bearer {app_token}"}
    h_fin = {"Authorization": f"Bearer {fin_token}"}

    # 1. Create a submitted invoice
    inv_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv_id),
        "company": "Vendor Beta",
        "total": 500.00,
        "submitter_id": sub_id,
        "status": InvoiceStatus.SUBMITTED,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "status_history": [{
            "invoice_id": inv_id,
            "previous_status": "draft",
            "new_status": InvoiceStatus.SUBMITTED,
            "user_id": sub_id,
            "role": "submitter",
            "timestamp": datetime.utcnow(),
            "reason": "Initial submission"
        }]
    })

    # Finance user CANNOT mark an unapproved (submitted) invoice as paid
    res_fin_early = client.post(f"/api/invoices/{inv_id}/paid", json={}, headers=h_fin)
    assert res_fin_early.status_code == 400
    assert "must be 'approved'" in res_fin_early.json["error"]

    # Finance user CANNOT approve or reject an invoice
    res_fin_app = client.post(f"/api/invoices/{inv_id}/approve", json={"comments": "ok"}, headers=h_fin)
    assert res_fin_app.status_code == 403
    res_fin_rej = client.post(f"/api/invoices/{inv_id}/reject", json={"reason": "not ok"}, headers=h_fin)
    assert res_fin_rej.status_code == 403

    # Approver CANNOT mark invoice as paid
    res_app_pay = client.post(f"/api/invoices/{inv_id}/paid", json={}, headers=h_app)
    assert res_app_pay.status_code == 403

    # Approver approves the invoice
    res_app_ok = client.post(f"/api/invoices/{inv_id}/approve", json={"comments": "Approved for payment"}, headers=h_app)
    assert res_app_ok.status_code == 200
    assert res_app_ok.json["invoice"]["status"] == InvoiceStatus.APPROVED

    # Verify history after approval
    doc = db_manager.db["invoices"].find_one({"_id": ObjectId(inv_id)})
    assert doc["status"] == InvoiceStatus.APPROVED
    assert len(doc["status_history"]) == 2
    app_hist = doc["status_history"][-1]
    assert app_hist["previous_status"] == InvoiceStatus.SUBMITTED
    assert app_hist["new_status"] == InvoiceStatus.APPROVED
    assert app_hist["user_id"] == app_id
    assert app_hist["role"] == "approver"
    assert "Approved for payment" in app_hist["reason"]

    # Now Finance User marks the approved invoice as paid
    res_fin_ok = client.post(f"/api/invoices/{inv_id}/paid", json={"payment_reference": "WIRE-778899"}, headers=h_fin)
    assert res_fin_ok.status_code == 200
    assert res_fin_ok.json["invoice"]["status"] == InvoiceStatus.PAID

    # Verify history after payment
    doc = db_manager.db["invoices"].find_one({"_id": ObjectId(inv_id)})
    assert doc["status"] == InvoiceStatus.PAID
    assert len(doc["status_history"]) == 3
    pay_hist = doc["status_history"][-1]
    assert pay_hist["previous_status"] == InvoiceStatus.APPROVED
    assert pay_hist["new_status"] == InvoiceStatus.PAID
    assert pay_hist["user_id"] == fin_id
    assert pay_hist["role"] == "finance"


def test_status_history_endpoint_and_immutability(client):
    """
    Verify GET /api/invoices/<id>/history:
    - Accessible to submitter and finance/approver/admin
    - Returns status_history and audit trail
    - Immutability: POST, PUT, PATCH, DELETE are strictly forbidden (403).
    """
    sub_token, sub_id = _get_token_for(client, f"sub_hist_{ObjectId()}@example.com", "Submitter Hist", UserRole.SUBMITTER)
    h_sub = {"Authorization": f"Bearer {sub_token}"}

    inv_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv_id),
        "company": "Vendor Gamma",
        "total": 120.00,
        "submitter_id": sub_id,
        "status": InvoiceStatus.SUBMITTED,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "status_history": [{
            "invoice_id": inv_id,
            "previous_status": "draft",
            "new_status": InvoiceStatus.SUBMITTED,
            "user_id": sub_id,
            "role": "submitter",
            "timestamp": datetime.utcnow(),
            "reason": "Created and submitted"
        }]
    })

    # 1. GET history returns status history
    get_res = client.get(f"/api/invoices/{inv_id}/history", headers=h_sub)
    assert get_res.status_code == 200
    assert "status_history" in get_res.json
    assert len(get_res.json["status_history"]) == 1
    assert get_res.json["status_history"][0]["new_status"] == InvoiceStatus.SUBMITTED

    # 2. Immutability checks: Mutation attempts return 403
    assert client.post(f"/api/invoices/{inv_id}/history", json={"fake": "edit"}, headers=h_sub).status_code == 403
    assert client.put(f"/api/invoices/{inv_id}/history", json={"fake": "replace"}, headers=h_sub).status_code == 403
    assert client.patch(f"/api/invoices/{inv_id}/history", json={"fake": "patch"}, headers=h_sub).status_code == 403
    assert client.delete(f"/api/invoices/{inv_id}/history", headers=h_sub).status_code == 403


def test_terminal_states_prevent_further_transitions(client):
    """Verify that cancelled invoices cannot be approved or marked as paid."""
    app_token, app_id = _get_token_for(client, f"app_term_{ObjectId()}@example.com", "Approver Term", UserRole.APPROVER)
    fin_token, fin_id = _get_token_for(client, f"fin_term_{ObjectId()}@example.com", "Finance Term", UserRole.FINANCE)
    h_app = {"Authorization": f"Bearer {app_token}"}
    h_fin = {"Authorization": f"Bearer {fin_token}"}

    inv_id = str(ObjectId())
    db_manager.db["invoices"].insert_one({
        "_id": ObjectId(inv_id),
        "company": "Vendor Delta",
        "total": 90.00,
        "submitter_id": str(ObjectId()),
        "status": InvoiceStatus.CANCELLED,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "status_history": []
    })

    # Attempt to approve cancelled invoice -> 400 Bad Request
    res_app = client.post(f"/api/invoices/{inv_id}/approve", json={"comments": "try to approve"}, headers=h_app)
    assert res_app.status_code == 400

    # Attempt to mark cancelled invoice as paid -> 400 Bad Request
    res_fin = client.post(f"/api/invoices/{inv_id}/paid", json={}, headers=h_fin)
    assert res_fin.status_code == 400
