"""Customer model for Accounts Receivable management."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class CustomerStatus(str, Enum):
    """Customer status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"

class Customer:
    """Customer model for AR invoices."""
    
    def __init__(
        self,
        name: str,
        status: str = CustomerStatus.ACTIVE,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        billing_address: Optional[str] = None,
        shipping_address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
        currency: Optional[str] = "USD",
        notes: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ):
        self._id = _id
        self.name = name
        self.status = status
        self.email = email
        self.phone = phone
        self.billing_address = billing_address
        self.shipping_address = shipping_address
        self.tax_id = tax_id
        self.payment_terms = payment_terms or "Net 30"
        self.currency = currency
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary for storage."""
        data = {
            "name": self.name,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "billing_address": self.billing_address,
            "shipping_address": self.shipping_address,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "currency": self.currency,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
        if self._id:
            data["_id"] = self._id
        return data
    
    def to_json(self) -> Dict[str, Any]:
        """Convert customer to JSON-safe dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "billing_address": self.billing_address,
            "shipping_address": self.shipping_address,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "currency": self.currency,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Customer':
        """Create Customer instance from dictionary."""
        return Customer(
            _id=str(data.get("_id")) if data.get("_id") else None,
            name=data["name"],
            status=data.get("status", CustomerStatus.ACTIVE),
            email=data.get("email"),
            phone=data.get("phone"),
            billing_address=data.get("billing_address"),
            shipping_address=data.get("shipping_address"),
            tax_id=data.get("tax_id"),
            payment_terms=data.get("payment_terms"),
            currency=data.get("currency", "USD"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            created_by=data.get("created_by")
        )
