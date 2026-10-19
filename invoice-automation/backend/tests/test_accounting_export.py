"""
Tests for Accounting Export Engine.
Covers balanced double-entry journal generation (Debits == Credits),
duplicate export prevention, and batch audit tracking.
"""

import pytest
from bson import ObjectId
from services.accounting_export_service import AccountingExportService


def test_balanced_double_entry_export(mongo_db):
    service = AccountingExportService(mongo_db)
    user_id = str(ObjectId())

    # Create approved invoices
    mongo_db["invoices"].insert_one({
        "invoice_number": "BILL-001",
        "company": "SaaS Provider Inc",
        "category": "software",
        "total": 1150.00,
        "subtotal": 1000.00,
        "tax_amount": 150.00,
        "discount": 0.00,
        "currency": "USD",
        "status": "approved"
    })

    mongo_db["invoices"].insert_one({
        "invoice_number": "BILL-002",
        "company": "Stationery Central",
        "category": "supplies",
        "total": 500.00,
        "subtotal": 500.00,
        "tax_amount": 0.00,
        "discount": 0.00,
        "currency": "USD",
        "status": "paid"
    })

    # Export batch
    succ, batch, csv_text, err = service.export_approved_invoices_batch(user_id=user_id)

    assert succ is True
    assert batch is not None
    assert batch["invoice_count"] == 2
    # Verify debits == credits balance
    assert batch["total_debits"] == batch["total_credits"]
    assert batch["total_debits"] == 1650.00
    assert "Entry ID" in csv_text
    assert "Operating Expense" in csv_text


def test_duplicate_export_prevention(mongo_db):
    service = AccountingExportService(mongo_db)
    user_id = str(ObjectId())

    mongo_db["invoices"].insert_one({
        "invoice_number": "BILL-DUP-EXP",
        "company": "Telecom Provider",
        "category": "general",
        "total": 300.00,
        "subtotal": 300.00,
        "tax_amount": 0.00,
        "currency": "USD",
        "status": "approved"
    })

    # First export
    s1, b1, c1, e1 = service.export_approved_invoices_batch(user_id=user_id)
    assert s1 is True

    # Second export attempt should find no unexported approved invoices
    s2, b2, c2, e2 = service.export_approved_invoices_batch(user_id=user_id, include_already_exported=False)
    assert s2 is False
    assert "No unexported" in e2
