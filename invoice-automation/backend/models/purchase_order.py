"""Purchase Order model and related enums for procurement and 3-way matching."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PurchaseOrderStatus(str, Enum):
    """Purchase Order lifecycle statuses."""
    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder:
    """Purchase Order domain entity."""

    def __init__(
        self,
        po_number: str,
        vendor_name: str,
        total_amount: float,
        line_items: List[Dict[str, Any]],
        vendor_id: Optional[str] = None,
        currency: str = "USD",
        status: str = PurchaseOrderStatus.OPEN,
        tolerance_percent: float = 5.0,
        notes: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = _id
        self.po_number = po_number.strip().upper()
        self.vendor_name = vendor_name.strip()
        self.total_amount = float(f"{total_amount:.2f}")
        self.line_items = line_items or []
        self.vendor_id = vendor_id
        self.currency = currency
        self.status = status
        self.tolerance_percent = float(tolerance_percent)
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "po_number": self.po_number,
            "vendor_name": self.vendor_name,
            "total_amount": self.total_amount,
            "line_items": self.line_items,
            "vendor_id": self.vendor_id,
            "currency": self.currency,
            "status": self.status,
            "tolerance_percent": self.tolerance_percent,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if self._id:
            data["_id"] = self._id
        return data

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": str(self._id) if self._id else None,
            "po_number": self.po_number,
            "vendor_name": self.vendor_name,
            "total_amount": self.total_amount,
            "line_items": self.line_items,
            "vendor_id": self.vendor_id,
            "currency": self.currency,
            "status": self.status,
            "tolerance_percent": self.tolerance_percent,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PurchaseOrder':
        return PurchaseOrder(
            _id=str(data.get("_id")) if data.get("_id") else None,
            po_number=data["po_number"],
            vendor_name=data["vendor_name"],
            total_amount=data["total_amount"],
            line_items=data.get("line_items", []),
            vendor_id=data.get("vendor_id"),
            currency=data.get("currency", "USD"),
            status=data.get("status", PurchaseOrderStatus.OPEN),
            tolerance_percent=data.get("tolerance_percent", 5.0),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
