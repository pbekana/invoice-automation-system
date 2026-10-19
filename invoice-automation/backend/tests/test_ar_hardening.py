"""
Tests for Accounts Receivable (AR) Hardening.
Covers Decimal line-item calculation, credit note applications,
aging analysis buckets, and customer account statements.
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from services.ar_service import ARService
from decimal import Decimal


def test_ar_decimal_calculation(mongo_db):
    service = ARService(mongo_db)

    line_items = [
        {"description": "Consulting Services", "quantity": 10, "unit_price": 150.25, "tax_rate": 15.0},
        {"description": "Travel Expenses", "quantity": 1, "unit_price": 340.50, "tax_rate": 0.0}
    ]
    # Consulting subtotal: 10 * 150.25 = 1502.50, tax: 1502.50 * 0.15 = 225.375 -> 225.38
    # Travel subtotal: 340.50, tax: 0.00
    # Expected subtotal = 1843.00, tax = 225.38, discount = 50.00, total = 2018.38

    subtotal, tax_amount, discount, total = service.calculate_invoice_totals(line_items, discount_val=50.00)

    assert subtotal == Decimal('1843.00')
    assert tax_amount == Decimal('225.38')
    assert discount == Decimal('50.00')
    assert total == Decimal('2018.38')


def test_ar_credit_note_application(mongo_db):
    service = ARService(mongo_db)
    user_id = str(ObjectId())

    inv_res = mongo_db["ar_invoices"].insert_one({
        "type": "receivable",
        "invoice_number": "AR-INV-500",
        "total": 1000.00,
        "outstanding_balance": 1000.00,
        "status": "sent"
    })
    invoice_id = str(inv_res.inserted_id)

    # Apply 400.00 credit note
    succ, cn, new_bal, err = service.apply_credit_note(
        invoice_id=invoice_id,
        amount=400.00,
        reason="Client discount concession",
        user_id=user_id
    )

    assert succ is True
    assert cn is not None
    assert new_bal == 600.00

    updated_inv = mongo_db["ar_invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert updated_inv["outstanding_balance"] == 600.00


def test_ar_aging_buckets(mongo_db):
    service = ARService(mongo_db)
    cust_id = str(ObjectId())
    today = datetime.utcnow().date()

    # 1. Current invoice (due in future)
    mongo_db["ar_invoices"].insert_one({
        "type": "receivable",
        "customer_id": cust_id,
        "customer_name": "Test Client Corp",
        "total": 1000.00,
        "outstanding_balance": 1000.00,
        "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
        "status": "sent"
    })

    # 2. 15 days overdue -> days_1_30
    mongo_db["ar_invoices"].insert_one({
        "type": "receivable",
        "customer_id": cust_id,
        "customer_name": "Test Client Corp",
        "total": 500.00,
        "outstanding_balance": 500.00,
        "due_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": "sent"
    })

    # 3. 45 days overdue -> days_31_60
    mongo_db["ar_invoices"].insert_one({
        "type": "receivable",
        "customer_id": cust_id,
        "customer_name": "Test Client Corp",
        "total": 300.00,
        "outstanding_balance": 300.00,
        "due_date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
        "status": "sent"
    })

    # 4. 100 days overdue -> days_90_plus
    mongo_db["ar_invoices"].insert_one({
        "type": "receivable",
        "customer_id": cust_id,
        "customer_name": "Test Client Corp",
        "total": 200.00,
        "outstanding_balance": 200.00,
        "due_date": (today - timedelta(days=100)).strftime("%Y-%m-%d"),
        "status": "sent"
    })

    report = service.get_aging_report(as_of_date=today.strftime("%Y-%m-%d"))

    assert report["total_outstanding"] == 2000.00
    buckets = report["aging_buckets"]
    assert buckets["current"] == 1000.00
    assert buckets["days_1_30"] == 500.00
    assert buckets["days_31_60"] == 300.00
    assert buckets["days_90_plus"] == 200.00
