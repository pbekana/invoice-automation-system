"""Payment model and related enums for authoritative financial recording."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment transaction statuses."""
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class PaymentMethod(str, Enum):
    """Payment methods."""
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    ELECTRONIC = "electronic"


class Payment:
    """Payment transaction entity."""

    def __init__(
        self,
        invoice_id: str,
        amount: float,
        payment_date: str,
        created_by: str,
        invoice_type: str = "payable",
        currency: str = "USD",
        payment_method: str = PaymentMethod.BANK_TRANSFER,
        transaction_reference: Optional[str] = None,
        external_reference: Optional[str] = None,
        status: str = PaymentStatus.COMPLETED,
        idempotency_key: Optional[str] = None,
        notes: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        reversed_at: Optional[datetime] = None,
        reversed_by: Optional[str] = None,
        reversal_reason: Optional[str] = None
    ):
        self._id = _id
        self.invoice_id = str(invoice_id)
        self.amount = float(f"{amount:.2f}")
        self.payment_date = payment_date
        self.created_by = str(created_by)
        self.invoice_type = invoice_type
        self.currency = currency
        self.payment_method = payment_method
        self.transaction_reference = transaction_reference
        self.external_reference = external_reference
        self.status = status
        self.idempotency_key = idempotency_key
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.reversed_at = reversed_at
        self.reversed_by = reversed_by
        self.reversal_reason = reversal_reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert payment to dictionary for MongoDB storage."""
        data = {
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "payment_date": self.payment_date,
            "created_by": self.created_by,
            "invoice_type": self.invoice_type,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "external_reference": self.external_reference,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "notes": self.notes,
            "created_at": self.created_at,
            "reversed_at": self.reversed_at,
            "reversed_by": self.reversed_by,
            "reversal_reason": self.reversal_reason
        }
        if self._id:
            data["_id"] = self._id
        return data

    def to_json(self) -> Dict[str, Any]:
        """Convert payment to JSON-safe dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "payment_date": self.payment_date,
            "created_by": self.created_by,
            "invoice_type": self.invoice_type,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "external_reference": self.external_reference,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reversed_at": self.reversed_at.isoformat() if self.reversed_at else None,
            "reversed_by": self.reversed_by,
            "reversal_reason": self.reversal_reason
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Payment':
        """Create Payment instance from dictionary."""
        return Payment(
            _id=str(data.get("_id")) if data.get("_id") else None,
            invoice_id=data["invoice_id"],
            amount=data["amount"],
            payment_date=data["payment_date"],
            created_by=data["created_by"],
            invoice_type=data.get("invoice_type", "payable"),
            currency=data.get("currency", "USD"),
            payment_method=data.get("payment_method", PaymentMethod.BANK_TRANSFER),
            transaction_reference=data.get("transaction_reference"),
            external_reference=data.get("external_reference"),
            status=data.get("status", PaymentStatus.COMPLETED),
            idempotency_key=data.get("idempotency_key"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            reversed_at=data.get("reversed_at"),
            reversed_by=data.get("reversed_by"),
            reversal_reason=data.get("reversal_reason")
        )
