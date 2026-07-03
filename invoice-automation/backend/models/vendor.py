"""Vendor model for supplier management."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class VendorStatus(str, Enum):
    """Vendor status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class Vendor:
    """Vendor/Supplier model."""
    
    def __init__(
        self,
        name: str,
        normalized_name: str,
        status: str = VendorStatus.ACTIVE,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
        default_category: Optional[str] = None,
        notes: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ):
        self._id = _id
        self.name = name
        self.normalized_name = normalized_name
        self.status = status
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id
        self.payment_terms = payment_terms or "Net 30"
        self.default_category = default_category
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vendor to dictionary for storage."""
        data = {
            "name": self.name,
            "normalized_name": self.normalized_name,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "default_category": self.default_category,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
        if self._id:
            data["_id"] = self._id
        return data
    
    def to_json(self) -> Dict[str, Any]:
        """Convert vendor to JSON-safe dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "default_category": self.default_category,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Vendor':
        """Create Vendor instance from dictionary."""
        return Vendor(
            _id=str(data.get("_id")) if data.get("_id") else None,
            name=data["name"],
            normalized_name=data["normalized_name"],
            status=data.get("status", VendorStatus.ACTIVE),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            tax_id=data.get("tax_id"),
            payment_terms=data.get("payment_terms"),
            default_category=data.get("default_category"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            created_by=data.get("created_by")
        )
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize vendor name for deduplication."""
        import re
        # Remove common suffixes
        name = re.sub(r'\b(Inc|LLC|Ltd|Corp|Corporation|Limited|Co)\b\.?', '', name, flags=re.IGNORECASE)
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name)
        # Lowercase and strip
        return name.lower().strip()
    
    def is_active(self) -> bool:
        """Check if vendor is active."""
        return self.status == VendorStatus.ACTIVE
    
    def is_blocked(self) -> bool:
        """Check if vendor is blocked."""
        return self.status == VendorStatus.BLOCKED
