"""
Tests for Authoritative Payment Recording Service.
Covers full payments, partial payments, overpayment prevention, idempotency, and reversals.
"""

import pytest
from decimal import Decimal
from bson import ObjectId
from services.payment_service import PaymentService
from models.payment import PaymentMethod, PaymentStatus
from models.invoice import InvoiceStatus
from utils.money import to_decimal


def test_payment_recording_full_payment(mongo_db):
    service = PaymentService(mongo_db)
    user_id = str(ObjectId())

    # Create test invoice
    inv_res = mongo_db["invoices"].insert_one({
        "company": "Vendor Alpha",
        "total": 50000.00,
        "currency": "ETB",
        "status": InvoiceStatus.APPROVED,
        "submitter_id": user_id
    })
    invoice_id = str(inv_res.inserted_id)

    # Record full payment
    success, payment, remaining_bal, error = service.record_payment(
        invoice_id=invoice_id,
        amount=50000.00,
        user_id=user_id,
        payment_method=PaymentMethod.BANK_TRANSFER,
        transaction_reference="TXN-FULL-001"
    )

    assert success is True
    assert payment is not None
    assert payment.amount == 50000.00
    assert remaining_bal == 0.0

    # Verify invoice status transitioned to PAID
    updated_inv = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert updated_inv["status"] == InvoiceStatus.PAID
    assert updated_inv["paid_amount"] == 50000.00
    assert updated_inv["outstanding_balance"] == 0.0


def test_payment_recording_partial_payments(mongo_db):
    service = PaymentService(mongo_db)
    user_id = str(ObjectId())

    # Create test invoice: total 50,000 ETB
    inv_res = mongo_db["invoices"].insert_one({
        "company": "Tech Logistics",
        "total": 50000.00,
        "currency": "ETB",
        "status": InvoiceStatus.APPROVED,
        "submitter_id": user_id
    })
    invoice_id = str(inv_res.inserted_id)

    # Payment 1: 20,000 ETB
    succ1, p1, rem1, err1 = service.record_payment(
        invoice_id=invoice_id,
        amount=20000.00,
        user_id=user_id,
        transaction_reference="PARTIAL-001"
    )
    assert succ1 is True
    assert rem1 == 30000.00

    inv_after_p1 = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert inv_after_p1["status"] == InvoiceStatus.PARTIALLY_PAID
    assert inv_after_p1["paid_amount"] == 20000.00
    assert inv_after_p1["outstanding_balance"] == 30000.00

    # Payment 2: 30,000 ETB
    succ2, p2, rem2, err2 = service.record_payment(
        invoice_id=invoice_id,
        amount=30000.00,
        user_id=user_id,
        transaction_reference="PARTIAL-002"
    )
    assert succ2 is True
    assert rem2 == 0.0

    inv_after_p2 = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert inv_after_p2["status"] == InvoiceStatus.PAID
    assert inv_after_p2["paid_amount"] == 50000.00
    assert inv_after_p2["outstanding_balance"] == 0.0


def test_payment_prevents_overpayment(mongo_db):
    service = PaymentService(mongo_db)
    user_id = str(ObjectId())

    inv_res = mongo_db["invoices"].insert_one({
        "company": "Stationery Hub",
        "total": 1000.00,
        "currency": "USD",
        "status": InvoiceStatus.APPROVED,
        "submitter_id": user_id
    })
    invoice_id = str(inv_res.inserted_id)

    # Attempt to pay 1,500 on 1,000 invoice
    success, payment, remaining_bal, error = service.record_payment(
        invoice_id=invoice_id,
        amount=1500.00,
        user_id=user_id
    )

    assert success is False
    assert "exceeds" in error.lower()


def test_payment_idempotency_control(mongo_db):
    service = PaymentService(mongo_db)
    user_id = str(ObjectId())

    inv_res = mongo_db["invoices"].insert_one({
        "company": "Cloud Services Inc",
        "total": 500.00,
        "currency": "USD",
        "status": InvoiceStatus.APPROVED,
        "submitter_id": user_id
    })
    invoice_id = str(inv_res.inserted_id)
    idempotency_key = "idemp-unique-xyz-123"

    # First attempt
    s1, p1, r1, e1 = service.record_payment(
        invoice_id=invoice_id,
        amount=500.00,
        user_id=user_id,
        idempotency_key=idempotency_key
    )
    assert s1 is True
    payment_id = str(p1._id)

    # Repeated identical attempt with same idempotency key
    s2, p2, r2, e2 = service.record_payment(
        invoice_id=invoice_id,
        amount=500.00,
        user_id=user_id,
        idempotency_key=idempotency_key
    )
    assert s2 is True
    assert str(p2._id) == payment_id
    # Ensure no second payment record was created
    assert mongo_db["payments"].count_documents({"invoice_id": invoice_id}) == 1


def test_payment_reversal(mongo_db):
    service = PaymentService(mongo_db)
    user_id = str(ObjectId())

    inv_res = mongo_db["invoices"].insert_one({
        "company": "Vendor Beta",
        "total": 2500.00,
        "currency": "USD",
        "status": InvoiceStatus.APPROVED,
        "submitter_id": user_id
    })
    invoice_id = str(inv_res.inserted_id)

    # Record payment
    s1, p1, r1, e1 = service.record_payment(
        invoice_id=invoice_id,
        amount=2500.00,
        user_id=user_id,
        transaction_reference="PAY-REV-01"
    )
    assert s1 is True
    payment_id = str(p1._id)

    # Reverse payment
    rev_succ, rev_p, new_bal, rev_err = service.reverse_payment(
        payment_id=payment_id,
        user_id=user_id,
        reversal_reason="Cheque returned due to signature discrepancy"
    )

    assert rev_succ is True
    assert rev_p.status == PaymentStatus.REVERSED
    assert rev_p.reversal_reason == "Cheque returned due to signature discrepancy"
    assert new_bal == 2500.00

    # Invoice balance restored and status reverted to approved
    updated_inv = mongo_db["invoices"].find_one({"_id": ObjectId(invoice_id)})
    assert updated_inv["status"] == InvoiceStatus.APPROVED
    assert updated_inv["paid_amount"] == 0.0
    assert updated_inv["outstanding_balance"] == 2500.00
