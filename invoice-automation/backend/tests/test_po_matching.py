"""
Tests for Purchase Order (PO) Matching Service.
Covers 2-way and 3-way matching, price variance, quantity variance,
matching tolerances, and non-PO invoice handling.
"""

import pytest
from services.po_matching_service import POMatchingService


def test_non_po_invoice_handling(mongo_db):
    service = POMatchingService(mongo_db)
    invoice_data = {
        "company": "Office Supplies Co",
        "total": 150.00,
        "currency": "USD"
    }

    result = service.match_invoice(invoice_data, po_number=None)
    assert result["matched"] is True
    assert result["has_po"] is False
    assert result["match_status"] == "no_po_required"
    assert len(result["discrepancies"]) == 0


def test_po_matching_within_tolerance(mongo_db):
    service = POMatchingService(mongo_db)

    # Create PO with 5% tolerance
    succ, po, err = service.create_purchase_order(
        po_number="PO-2026-101",
        vendor_name="Hardware Warehouse",
        total_amount=1000.00,
        line_items=[{
            "description": "Ergonomic Chairs",
            "quantity_ordered": 10,
            "quantity_received": 10,
            "unit_price": 100.00
        }],
        tolerance_percent=5.0
    )
    assert succ is True

    # Invoice matching PO within tolerance (total 1040 <= 1050 allowed)
    invoice_data = {
        "purchase_order_number": "PO-2026-101",
        "currency": "USD",
        "total": 1040.00,
        "line_items": [{
            "description": "Ergonomic Chairs",
            "quantity": 10,
            "unit_price": 100.00
        }]
    }

    result = service.match_invoice(invoice_data)
    assert result["matched"] is True
    assert result["match_status"] == "matched"
    assert len(result["discrepancies"]) == 0


def test_po_matching_price_variance_exception(mongo_db):
    service = POMatchingService(mongo_db)

    # Create PO with authorized unit price of 50.00
    service.create_purchase_order(
        po_number="PO-PRICE-TEST",
        vendor_name="Widget Corp",
        total_amount=500.00,
        line_items=[{
            "description": "Standard Widgets",
            "quantity_ordered": 10,
            "quantity_received": 10,
            "unit_price": 50.00
        }],
        tolerance_percent=2.0
    )

    # Invoice billed unit price at 60.00 (exceeds authorized unit price)
    invoice_data = {
        "purchase_order_number": "PO-PRICE-TEST",
        "currency": "USD",
        "total": 600.00,
        "line_items": [{
            "description": "Standard Widgets",
            "quantity": 10,
            "unit_price": 60.00
        }]
    }

    result = service.match_invoice(invoice_data)
    assert result["matched"] is False
    assert result["match_status"] == "discrepancy_exception"
    assert any("Price variance" in d for d in result["discrepancies"])


def test_po_matching_quantity_variance_exception(mongo_db):
    service = POMatchingService(mongo_db)

    # Create PO with 10 ordered, but only 5 goods receipts recorded
    service.create_purchase_order(
        po_number="PO-QTY-TEST",
        vendor_name="Paper Supply Inc",
        total_amount=200.00,
        line_items=[{
            "description": "A4 Paper Reams",
            "quantity_ordered": 10,
            "quantity_received": 5,
            "unit_price": 20.00
        }],
        tolerance_percent=0.0
    )

    # Invoice claims 10 reams (exceeds received quantity of 5)
    invoice_data = {
        "purchase_order_number": "PO-QTY-TEST",
        "currency": "USD",
        "total": 200.00,
        "line_items": [{
            "description": "A4 Paper Reams",
            "quantity": 10,
            "unit_price": 20.00
        }]
    }

    result = service.match_invoice(invoice_data)
    assert result["matched"] is False
    assert result["match_status"] == "discrepancy_exception"
    assert any("Quantity variance" in d for d in result["discrepancies"])
