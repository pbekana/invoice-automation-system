"""Credit Note model for Accounts Receivable adjustments."""
from datetime import datetime
from typing import Optional, Dict, Any


class CreditNote:
    """Credit Note entity reducing customer receivable balances."""

    def __init__(
        self,
        credit_note_number: str,
        invoice_id: str,
        customer_id: str,
        amount: float,
        reason: str,
        created_by: str,
        currency: str = "USD",
        date: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = _id
        self.credit_note_number = credit_note_number.strip().upper()
        self.invoice_id = str(invoice_id)
        self.customer_id = str(customer_id)
        self.amount = float(f"{amount:.2f}")
        self.reason = reason.strip()
        self.created_by = str(created_by)
        self.currency = currency
        self.date = date or datetime.utcnow().strftime("%Y-%m-%d")
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "credit_note_number": self.credit_note_number,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "reason": self.reason,
            "created_by": self.created_by,
            "currency": self.currency,
            "date": self.date,
            "created_at": self.created_at
        }
        if self._id:
            data["_id"] = self._id
        return data

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": str(self._id) if self._id else None,
            "credit_note_number": self.credit_note_number,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "reason": self.reason,
            "created_by": self.created_by,
            "currency": self.currency,
            "date": self.date,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CreditNote':
        return CreditNote(
            _id=str(data.get("_id")) if data.get("_id") else None,
            credit_note_number=data["credit_note_number"],
            invoice_id=data["invoice_id"],
            customer_id=data["customer_id"],
            amount=data["amount"],
            reason=data["reason"],
            created_by=data["created_by"],
            currency=data.get("currency", "USD"),
            date=data.get("date"),
            created_at=data.get("created_at")
        )
