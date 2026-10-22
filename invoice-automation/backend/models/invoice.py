"""Invoice model and related enums."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice workflow statuses."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class ApprovalStatus(str, Enum):
    """Individual approval statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Invoice:
    """Invoice model with workflow, financial fields, and audit support."""

    def __init__(
        self,
        company: str,
        date: Optional[str],
        total: float,
        category: str,
        submitter_id: str,
        status: str = InvoiceStatus.SUBMITTED,
        vendor_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        due_date: Optional[str] = None,
        currency: str = "USD",
        subtotal: Optional[float] = None,
        tax_amount: float = 0.0,
        tax_rate: float = 0.0,
        discount: float = 0.0,
        paid_amount: float = 0.0,
        outstanding_balance: Optional[float] = None,
        payment_terms: Optional[str] = None,
        purchase_order_number: Optional[str] = None,
        po_match_status: Optional[str] = None,
        duplicate_status: Optional[str] = None,
        sha256_hash: Optional[str] = None,
        storage_key: Optional[str] = None,
        original_filename: Optional[str] = None,
        validation: Optional[Dict[str, Any]] = None,
        raw_text: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
        approval_chain: Optional[List[Dict[str, Any]]] = None,
        status_history: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        approved_at: Optional[datetime] = None,
        paid_at: Optional[datetime] = None
    ):
        self._id = _id
        self.company = company
        self.date = date
        self.total = float(f"{total:.2f}") if total is not None else 0.0
        self.category = category
        self.submitter_id = str(submitter_id) if submitter_id else ""
        self.status = status
        self.vendor_id = vendor_id
        self.invoice_number = invoice_number
        self.due_date = due_date
        self.currency = currency or "USD"
        self.subtotal = float(f"{subtotal:.2f}") if subtotal is not None else self.total
        self.tax_amount = float(f"{tax_amount:.2f}") if tax_amount is not None else 0.0
        self.tax_rate = float(tax_rate) if tax_rate is not None else 0.0
        self.discount = float(f"{discount:.2f}") if discount is not None else 0.0
        self.paid_amount = float(f"{paid_amount:.2f}") if paid_amount is not None else 0.0
        if outstanding_balance is not None:
            self.outstanding_balance = float(f"{outstanding_balance:.2f}")
        else:
            self.outstanding_balance = max(0.0, float(f"{(self.total - self.paid_amount):.2f}"))
        self.payment_terms = payment_terms
        self.purchase_order_number = purchase_order_number
        self.po_match_status = po_match_status
        self.duplicate_status = duplicate_status
        self.sha256_hash = sha256_hash
        self.storage_key = storage_key
        self.original_filename = original_filename
        self.validation = validation or {}
        self.raw_text = raw_text
        self.confidence = confidence or {}
        self.line_items = line_items or []
        self.approval_chain = approval_chain or []
        self.status_history = status_history or []
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.approved_at = approved_at
        self.paid_at = paid_at

    @property
    def is_overdue(self) -> bool:
        """Dynamically determine if invoice is past due date with outstanding balance."""
        if not self.due_date:
            return False
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        try:
            due = datetime.strptime(str(self.due_date)[:10], "%Y-%m-%d").date()
            bal = self.outstanding_balance if self.outstanding_balance is not None else self.total
            return datetime.utcnow().date() > due and bal > 0
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary for MongoDB storage."""
        data = {
            "company": self.company,
            "date": self.date,
            "total": self.total,
            "category": self.category,
            "submitter_id": self.submitter_id,
            "status": self.status,
            "vendor_id": self.vendor_id,
            "invoice_number": self.invoice_number,
            "due_date": self.due_date,
            "currency": self.currency,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "tax_rate": self.tax_rate,
            "discount": self.discount,
            "paid_amount": self.paid_amount,
            "outstanding_balance": self.outstanding_balance,
            "payment_terms": self.payment_terms,
            "purchase_order_number": self.purchase_order_number,
            "po_match_status": self.po_match_status,
            "duplicate_status": self.duplicate_status,
            "sha256_hash": self.sha256_hash,
            "storage_key": self.storage_key,
            "original_filename": self.original_filename,
            "validation": self.validation,
            "is_overdue": self.is_overdue,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "line_items": self.line_items,
            "approval_chain": self.approval_chain,
            "status_history": self.status_history,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_at": self.approved_at,
            "paid_at": self.paid_at
        }
        if self._id:
            data["_id"] = self._id
        return data

    def to_json(self) -> Dict[str, Any]:
        """Convert invoice to JSON-safe dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "company": self.company,
            "date": self.date,
            "total": self.total,
            "category": self.category,
            "submitter_id": self.submitter_id,
            "status": self.status,
            "vendor_id": self.vendor_id,
            "invoice_number": self.invoice_number,
            "due_date": self.due_date,
            "currency": self.currency,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "tax_rate": self.tax_rate,
            "discount": self.discount,
            "paid_amount": self.paid_amount,
            "outstanding_balance": self.outstanding_balance,
            "payment_terms": self.payment_terms,
            "purchase_order_number": self.purchase_order_number,
            "po_match_status": self.po_match_status,
            "duplicate_status": self.duplicate_status,
            "sha256_hash": self.sha256_hash,
            "storage_key": self.storage_key,
            "original_filename": self.original_filename,
            "validation": self.validation,
            "is_overdue": self.is_overdue,
            "confidence": self.confidence,
            "line_items": self.line_items,
            "approval_chain": self.approval_chain,
            "status_history": [
                {
                    **h,
                    "timestamp": h["timestamp"].isoformat() if isinstance(h.get("timestamp"), datetime) else h.get("timestamp")
                }
                for h in (self.status_history or [])
            ],
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Invoice':
        """Create Invoice instance from dictionary."""
        return Invoice(
            _id=str(data.get("_id")) if data.get("_id") else None,
            company=data.get("company", "Unknown"),
            date=data.get("date"),
            total=data.get("total", 0.0),
            category=data.get("category", "General"),
            submitter_id=data.get("submitter_id", ""),
            status=data.get("status", InvoiceStatus.SUBMITTED),
            vendor_id=data.get("vendor_id"),
            invoice_number=data.get("invoice_number"),
            due_date=data.get("due_date"),
            currency=data.get("currency", "USD"),
            subtotal=data.get("subtotal"),
            tax_amount=data.get("tax_amount", 0.0),
            tax_rate=data.get("tax_rate", 0.0),
            discount=data.get("discount", 0.0),
            paid_amount=data.get("paid_amount", 0.0),
            outstanding_balance=data.get("outstanding_balance"),
            payment_terms=data.get("payment_terms"),
            purchase_order_number=data.get("purchase_order_number"),
            po_match_status=data.get("po_match_status"),
            duplicate_status=data.get("duplicate_status"),
            sha256_hash=data.get("sha256_hash"),
            storage_key=data.get("storage_key"),
            original_filename=data.get("original_filename"),
            validation=data.get("validation", {}),
            raw_text=data.get("raw_text"),
            confidence=data.get("confidence", {}),
            line_items=data.get("line_items", []),
            approval_chain=data.get("approval_chain", []),
            status_history=data.get("status_history", []),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            approved_at=data.get("approved_at"),
            paid_at=data.get("paid_at")
        )

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new status is valid in the workflow state machine."""
        valid_transitions = {
            InvoiceStatus.DRAFT: [InvoiceStatus.SUBMITTED, InvoiceStatus.PENDING_APPROVAL, InvoiceStatus.CANCELLED],
            InvoiceStatus.PENDING: [
                InvoiceStatus.PENDING_APPROVAL,
                InvoiceStatus.APPROVED,
                InvoiceStatus.REJECTED,
                InvoiceStatus.NEEDS_REVISION,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.SUBMITTED: [
                InvoiceStatus.PENDING_APPROVAL,
                InvoiceStatus.APPROVED,
                InvoiceStatus.REJECTED,
                InvoiceStatus.NEEDS_REVISION,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.PENDING_APPROVAL: [
                InvoiceStatus.APPROVED,
                InvoiceStatus.REJECTED,
                InvoiceStatus.NEEDS_REVISION,
                InvoiceStatus.SUBMITTED,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.APPROVED: [
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.PAID,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.REJECTED: [
                InvoiceStatus.SUBMITTED,
                InvoiceStatus.PENDING_APPROVAL,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.NEEDS_REVISION: [
                InvoiceStatus.SUBMITTED,
                InvoiceStatus.PENDING_APPROVAL,
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.PARTIALLY_PAID: [
                InvoiceStatus.PAID,
                InvoiceStatus.APPROVED,  # Upon full payment reversal
                InvoiceStatus.CANCELLED
            ],
            InvoiceStatus.PAID: [
                InvoiceStatus.PARTIALLY_PAID,  # Upon partial reversal
                InvoiceStatus.APPROVED  # Upon full reversal
            ],
            InvoiceStatus.CANCELLED: []  # Terminal state
        }
        return new_status in valid_transitions.get(self.status, [])

    def is_editable(self) -> bool:
        """Check if invoice can be edited."""
        return self.status in [InvoiceStatus.DRAFT, InvoiceStatus.SUBMITTED, InvoiceStatus.REJECTED, InvoiceStatus.NEEDS_REVISION]

    def is_pending(self) -> bool:
        """Check if invoice is pending approval."""
        return self.status == InvoiceStatus.PENDING_APPROVAL

    def is_approved(self) -> bool:
        """Check if invoice is approved."""
        return self.status == InvoiceStatus.APPROVED

    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.PAID

    def add_approval(self, approver_id: str, status: str, comments: Optional[str] = None):
        """Add an approval decision to the chain."""
        approval = {
            "approver_id": str(approver_id),
            "status": status,
            "comments": comments,
            "timestamp": datetime.utcnow()
        }
        self.approval_chain.append(approval)
        self.updated_at = datetime.utcnow()

    def get_pending_approvers(self) -> List[str]:
        """Get list of approver IDs who haven't acted yet."""
        return []

    def has_approver_acted(self, approver_id: str) -> bool:
        """Check if a specific approver has already acted in the current approval round."""
        last_submit_time = None
        for a in reversed(self.approval_chain):
            if a.get("status") in [InvoiceStatus.SUBMITTED, InvoiceStatus.PENDING_APPROVAL]:
                last_submit_time = a.get("timestamp")
                break

        for a in self.approval_chain:
            if a.get("status") in [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED]:
                if str(a.get("approver_id")) == str(approver_id):
                    t = a.get("timestamp")
                    if not last_submit_time or (t and t >= last_submit_time):
                        return True
        return False
