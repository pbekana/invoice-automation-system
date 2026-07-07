"""Company model for tenant profile management."""
from datetime import datetime
from typing import Optional, Dict, Any

class Company:
    """Company profile model (the tenant's own company)."""
    
    def __init__(
        self,
        name: str,
        owner_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        logo_url: Optional[str] = None,
        currency: str = "USD",
        invoice_prefix: str = "INV-",
        payment_instructions: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = _id
        self.name = name
        self.owner_id = owner_id
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id
        self.logo_url = logo_url
        self.currency = currency
        self.invoice_prefix = invoice_prefix
        self.payment_instructions = payment_instructions
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "owner_id": self.owner_id,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "logo_url": self.logo_url,
            "currency": self.currency,
            "invoice_prefix": self.invoice_prefix,
            "payment_instructions": self.payment_instructions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if self._id:
            data["_id"] = self._id
        return data
    
    def to_json(self) -> Dict[str, Any]:
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "owner_id": str(self.owner_id),
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "logo_url": self.logo_url,
            "currency": self.currency,
            "invoice_prefix": self.invoice_prefix,
            "payment_instructions": self.payment_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Company':
        return Company(
            _id=str(data.get("_id")) if data.get("_id") else None,
            name=data["name"],
            owner_id=data["owner_id"],
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            tax_id=data.get("tax_id"),
            logo_url=data.get("logo_url"),
            currency=data.get("currency", "USD"),
            invoice_prefix=data.get("invoice_prefix", "INV-"),
            payment_instructions=data.get("payment_instructions"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
