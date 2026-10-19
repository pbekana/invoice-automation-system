"""
Tests for Application Security and Internal Controls.
Covers Segregation of Duties (self-approval prevention),
file signature magic-byte verification, and AI assistant role-scoping.
"""

import pytest
from bson import ObjectId
from services.invoice_service import InvoiceService
from services.document_storage_service import DocumentStorageService
from services.fallback_ai_service import FallbackAIService


def test_self_approval_prevention(mongo_db):
    invoice_service = InvoiceService(mongo_db)
    user_id = str(ObjectId())

    # Create invoice submitted by user_id
    succ, invoice, err = invoice_service.create_invoice(
        company="Self Approval Test Corp",
        date="2026-10-19",
        total=500.00,
        category="Supplies",
        submitter_id=user_id,
        status="pending"
    )
    assert succ is True
    invoice_id = str(invoice._id)

    # Submit invoice for approval
    sub_succ, sub_err = invoice_service.submit_invoice(invoice_id, user_id)
    assert sub_succ is True

    # Attempt to self-approve with same user_id
    app_succ, app_err = invoice_service.approve_invoice(
        invoice_id=invoice_id,
        approver_id=user_id,
        comments="Attempting self approval"
    )

    assert app_succ is False
    assert "Segregation of duties" in app_err
    assert "cannot approve their own" in app_err


def test_magic_byte_file_signature_validation():
    storage = DocumentStorageService()

    # Valid PDF signature
    pdf_bytes = b"%PDF-1.4\n%...\ntrailer\n%%EOF"
    v1, m1, e1 = storage.validate_file_signature(pdf_bytes, "invoice.pdf")
    assert v1 is True
    assert m1 == "application/pdf"

    # Malicious executable disguised as a PDF
    fake_pdf_bytes = b"MZ\x90\x00\x03\x00\x00\x00"  # Windows DOS/PE executable header
    v2, m2, e2 = storage.validate_file_signature(fake_pdf_bytes, "invoice.pdf")
    assert v2 is False
    assert "signature" in e2.lower()

    # Empty content
    v3, m3, e3 = storage.validate_file_signature(b"", "invoice.pdf")
    assert v3 is False
    assert "Empty" in e3


def test_fallback_ai_role_scoping(mongo_db):
    class MockDBManager:
        def __init__(self, db):
            self.db = db

    ai_service = FallbackAIService(MockDBManager(mongo_db))

    user1_id = str(ObjectId())
    user2_id = str(ObjectId())

    # Create user1 as submitter
    mongo_db["users"].insert_one({
        "_id": ObjectId(user1_id),
        "email": "submitter@example.com",
        "roles": ["submitter"]
    })

    # Create invoices for user1 and user2
    mongo_db["invoices"].insert_one({
        "invoice_number": "USER1-INV",
        "company": "Vendor One",
        "total": 100.00,
        "submitter_id": user1_id,
        "status": "pending"
    })
    mongo_db["invoices"].insert_one({
        "invoice_number": "USER2-INV",
        "company": "Vendor Two",
        "total": 900.00,
        "submitter_id": user2_id,
        "status": "pending"
    })

    # Submitter queries count -> should only see their own 1 invoice
    count_resp = ai_service._handle_invoice_count(user_id=user1_id)
    assert "1 invoices" in count_resp["response"]

    # Submitter queries spending -> should only see $100.00
    spend_resp = ai_service._handle_total_spending(user_id=user1_id)
    assert "$100.00" in spend_resp["response"]
