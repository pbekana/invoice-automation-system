"""Tests for invoice workflow functionality."""
import pytest
from models.invoice import Invoice, InvoiceStatus
from services.invoice_service import InvoiceService
from datetime import datetime


def test_invoice_status_transitions():
    """Test invoice status state machine."""
    invoice = Invoice(
        company="Test Co",
        date="2026-07-01",
        total=100.0,
        category="Supplies",
        submitter_id="user123",
        status=InvoiceStatus.SUBMITTED
    )
    
    # Valid transitions
    assert invoice.can_transition_to(InvoiceStatus.PENDING_APPROVAL)
    assert invoice.can_transition_to(InvoiceStatus.APPROVED)
    assert invoice.can_transition_to(InvoiceStatus.REJECTED)
    assert invoice.can_transition_to(InvoiceStatus.CANCELLED)
    
    # Invalid transitions
    assert not invoice.can_transition_to(InvoiceStatus.PAID)
    assert not invoice.can_transition_to(InvoiceStatus.DRAFT)


def test_invoice_editability():
    """Test invoice edit permissions by status."""
    # Editable statuses
    draft = Invoice(
        company="Test", date="2026-07-01", total=100, category="Food",
        submitter_id="user123", status=InvoiceStatus.DRAFT
    )
    assert draft.is_editable()
    
    submitted = Invoice(
        company="Test", date="2026-07-01", total=100, category="Food",
        submitter_id="user123", status=InvoiceStatus.SUBMITTED
    )
    assert submitted.is_editable()
    
    rejected = Invoice(
        company="Test", date="2026-07-01", total=100, category="Food",
        submitter_id="user123", status=InvoiceStatus.REJECTED
    )
    assert rejected.is_editable()
    
    # Non-editable statuses
    approved = Invoice(
        company="Test", date="2026-07-01", total=100, category="Food",
        submitter_id="user123", status=InvoiceStatus.APPROVED
    )
    assert not approved.is_editable()
    
    paid = Invoice(
        company="Test", date="2026-07-01", total=100, category="Food",
        submitter_id="user123", status=InvoiceStatus.PAID
    )
    assert not paid.is_editable()


def test_invoice_approval_chain():
    """Test approval chain tracking."""
    invoice = Invoice(
        company="Test Co",
        date="2026-07-01",
        total=100.0,
        category="Supplies",
        submitter_id="user123",
        status=InvoiceStatus.PENDING_APPROVAL
    )
    
    # Add approval
    invoice.add_approval("approver1", "approved", "Looks good")
    
    assert len(invoice.approval_chain) == 1
    assert invoice.approval_chain[0]["approver_id"] == "approver1"
    assert invoice.approval_chain[0]["status"] == "approved"
    assert invoice.approval_chain[0]["comments"] == "Looks good"
    
    # Check if approver acted
    assert invoice.has_approver_acted("approver1")
    assert not invoice.has_approver_acted("approver2")


def test_invoice_to_json():
    """Test invoice serialization."""
    invoice = Invoice(
        _id="123",
        company="Test Co",
        date="2026-07-01",
        total=150.50,
        category="Transport",
        submitter_id="user123",
        vendor_id="vendor456",
        invoice_number="INV-001",
        status=InvoiceStatus.APPROVED
    )
    
    json_data = invoice.to_json()
    
    assert json_data["id"] == "123"
    assert json_data["company"] == "Test Co"
    assert json_data["total"] == 150.50
    assert json_data["category"] == "Transport"
    assert json_data["status"] == InvoiceStatus.APPROVED
    assert json_data["vendor_id"] == "vendor456"
    assert json_data["invoice_number"] == "INV-001"
