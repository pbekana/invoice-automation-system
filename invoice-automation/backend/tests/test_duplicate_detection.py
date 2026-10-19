"""
Tests for Multi-Signal Duplicate Detection Service.
Covers document hash matching, normalized invoice number comparison,
date and amount proximity, and investigation resolution workflows.
"""

import pytest
from bson import ObjectId
from services.duplicate_detection_service import DuplicateDetectionService, DuplicateMatchLevel


def test_normalized_invoice_numbers():
    assert DuplicateDetectionService.normalize_invoice_number("INV-00042") == "42"
    assert DuplicateDetectionService.normalize_invoice_number("#00123-A") == "123A"
    assert DuplicateDetectionService.normalize_invoice_number("inv/2026/0009") == "20269"
    assert DuplicateDetectionService.normalize_invoice_number("0000") == "0"
    assert DuplicateDetectionService.normalize_invoice_number(None) == ""


def test_sha256_binary_fingerprint_duplicate(mongo_db):
    service = DuplicateDetectionService(mongo_db)
    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Insert existing invoice
    mongo_db["invoices"].insert_one({
        "invoice_number": "INV-100",
        "company": "Acme Supplies",
        "total": 350.00,
        "date": "2026-10-01",
        "sha256_hash": sha256,
        "status": "approved"
    })

    # Check incoming invoice with same sha256 fingerprint
    result = service.check_invoice(
        invoice_number="DIFFERENT-NUM",
        vendor_id=None,
        company="Different Name",
        total=350.00,
        date_str="2026-10-01",
        sha256_hash=sha256
    )

    assert result["has_duplicate"] is True
    assert result["match_level"] == DuplicateMatchLevel.DEFINITE
    assert any("Exact document binary fingerprint" in m["reason"] for m in result["matches"])


def test_vendor_and_normalized_number_duplicate(mongo_db):
    service = DuplicateDetectionService(mongo_db)
    vendor_id = str(ObjectId())

    mongo_db["invoices"].insert_one({
        "invoice_number": "INV-000456",
        "normalized_invoice_number": "456",
        "vendor_id": vendor_id,
        "company": "Apex Corp",
        "total": 1200.00,
        "date": "2026-09-15",
        "status": "pending"
    })

    # Incoming invoice with formatted number "456" or "INV-456"
    result = service.check_invoice(
        invoice_number="INV-456",
        vendor_id=vendor_id,
        company="Apex Corp",
        total=1200.00,
        date_str="2026-09-15"
    )

    assert result["has_duplicate"] is True
    assert result["match_level"] == DuplicateMatchLevel.DEFINITE
    assert any("Normalized invoice number" in m["reason"] for m in result["matches"])


def test_duplicate_investigation_resolution(mongo_db):
    service = DuplicateDetectionService(mongo_db)
    user_id = str(ObjectId())

    inv_res = mongo_db["invoices"].insert_one({
        "invoice_number": "INV-DUP-999",
        "company": "Sample Vendor",
        "total": 850.00,
        "status": "pending",
        "duplicate_status": "potential_duplicate"
    })
    invoice_id = str(inv_res.inserted_id)

    # 1. Resolve as cleared false positive
    succ1, err1 = service.resolve_duplicate_investigation(
        invoice_id=invoice_id,
        user_id=user_id,
        resolution="cleared_false_positive",
        investigation_notes="Legitimate recurring monthly fee for different service periods"
    )
    assert succ1 is True
    inv_cleared = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert inv_cleared["duplicate_status"] == "cleared"
    assert inv_cleared["duplicate_investigation"]["resolution"] == "cleared_false_positive"

    # 2. Resolve as confirmed duplicate
    succ2, err2 = service.resolve_duplicate_investigation(
        invoice_id=invoice_id,
        user_id=user_id,
        resolution="confirmed_duplicate",
        investigation_notes="Confirmed duplicate submission from supplier"
    )
    assert succ2 is True
    inv_cancelled = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert inv_cancelled["status"] == "cancelled"
    assert "Confirmed duplicate" in inv_cancelled["cancelled_reason"]
