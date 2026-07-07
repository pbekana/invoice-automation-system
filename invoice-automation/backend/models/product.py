"""Product model for Services and Items."""
from datetime import datetime
from typing import Optional, Dict, Any

class Product:
    """Product or Service model."""
    
    def __init__(
        self,
        name: str,
        sku: Optional[str] = None,
        description: Optional[str] = None,
        unit_price: float = 0.0,
        tax_rate: float = 0.0,
        category: Optional[str] = None,
        is_active: bool = True,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ):
        self._id = _id
        self.name = name
        self.sku = sku
        self.description = description
        self.unit_price = float(unit_price)
        self.tax_rate = float(tax_rate)
        self.category = category
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary for storage."""
        data = {
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "unit_price": self.unit_price,
            "tax_rate": self.tax_rate,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
        if self._id:
            data["_id"] = self._id
        return data
    
    def to_json(self) -> Dict[str, Any]:
        """Convert product to JSON-safe dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "unit_price": self.unit_price,
            "tax_rate": self.tax_rate,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Product':
        """Create Product instance from dictionary."""
        return Product(
            _id=str(data.get("_id")) if data.get("_id") else None,
            name=data["name"],
            sku=data.get("sku"),
            description=data.get("description"),
            unit_price=data.get("unit_price", 0.0),
            tax_rate=data.get("tax_rate", 0.0),
            category=data.get("category"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            created_by=data.get("created_by")
        )
