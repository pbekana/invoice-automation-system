"""Tests for vendor functionality."""
import pytest
from models.vendor import Vendor, VendorStatus


def test_vendor_name_normalization():
    """Test vendor name normalization for deduplication."""
    # Test removing common suffixes
    assert Vendor.normalize_name("Amazon.com, Inc.") == "amazon"
    assert Vendor.normalize_name("Google LLC") == "google"
    assert Vendor.normalize_name("Microsoft Corporation") == "microsoft"
    assert Vendor.normalize_name("Acme Corp.") == "acme"
    
    # Test punctuation removal
    assert Vendor.normalize_name("AT&T") == "att"
    assert Vendor.normalize_name("Smith & Co.") == "smith"
    
    # Test whitespace normalization
    assert Vendor.normalize_name("  Multiple   Spaces  Inc  ") == "multiple spaces"
    
    # Test case insensitivity
    assert Vendor.normalize_name("UPPERCASE INC") == "uppercase"
    assert Vendor.normalize_name("lowercase llc") == "lowercase"


def test_vendor_status_checks():
    """Test vendor status helper methods."""
    active = Vendor(
        name="Active Vendor",
        normalized_name="active vendor",
        status=VendorStatus.ACTIVE
    )
    assert active.is_active()
    assert not active.is_blocked()
    
    blocked = Vendor(
        name="Blocked Vendor",
        normalized_name="blocked vendor",
        status=VendorStatus.BLOCKED
    )
    assert not blocked.is_active()
    assert blocked.is_blocked()
    
    inactive = Vendor(
        name="Inactive Vendor",
        normalized_name="inactive vendor",
        status=VendorStatus.INACTIVE
    )
    assert not inactive.is_active()
    assert not inactive.is_blocked()


def test_vendor_to_json():
    """Test vendor serialization."""
    vendor = Vendor(
        _id="456",
        name="Test Vendor Inc.",
        normalized_name="test vendor",
        email="vendor@test.com",
        phone="555-1234",
        tax_id="12-3456789",
        payment_terms="Net 30",
        status=VendorStatus.ACTIVE
    )
    
    json_data = vendor.to_json()
    
    assert json_data["id"] == "456"
    assert json_data["name"] == "Test Vendor Inc."
    assert json_data["email"] == "vendor@test.com"
    assert json_data["phone"] == "555-1234"
    assert json_data["tax_id"] == "12-3456789"
    assert json_data["payment_terms"] == "Net 30"
    assert json_data["status"] == VendorStatus.ACTIVE


def test_vendor_from_dict():
    """Test vendor deserialization."""
    data = {
        "_id": "789",
        "name": "Deserialized Vendor",
        "normalized_name": "deserialized vendor",
        "email": "test@vendor.com",
        "status": VendorStatus.ACTIVE,
        "payment_terms": "Net 45"
    }
    
    vendor = Vendor.from_dict(data)
    
    assert vendor._id == "789"
    assert vendor.name == "Deserialized Vendor"
    assert vendor.normalized_name == "deserialized vendor"
    assert vendor.email == "test@vendor.com"
    assert vendor.status == VendorStatus.ACTIVE
    assert vendor.payment_terms == "Net 45"
