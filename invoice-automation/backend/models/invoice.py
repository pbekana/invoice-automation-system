"""Invoice model and related enums."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice workflow statuses."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Individual approval statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Invoice:
    """Invoice model with workflow support."""
    
    def __init__(
        self,
        company: str,
        date: str,
        total: float,
        category: str,
        submitter_id: str,
        status: str = InvoiceStatus.SUBMITTED,
        vendor_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        due_date: Optional[str] = None,
        raw_text: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
        approval_chain: Optional[List[Dict[str, Any]]] = None,
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
        self.total = total
        self.category = category
        self.submitter_id = submitter_id
        self.status = status
        self.vendor_id = vendor_id
        self.invoice_number = invoice_number
        self.due_date = due_date
        self.raw_text = raw_text
        self.confidence = confidence or {}
        self.line_items = line_items or []
        self.approval_chain = approval_chain or []
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.approved_at = approved_at
        self.paid_at = paid_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary for storage."""
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
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "line_items": self.line_items,
            "approval_chain": self.approval_chain,
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
            "confidence": self.confidence,
            "line_items": self.line_items,
            "approval_chain": self.approval_chain,
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
            company=data["company"],
            date=data["date"],
            total=data["total"],
            category=data["category"],
            submitter_id=data["submitter_id"],
            status=data.get("status", InvoiceStatus.SUBMITTED),
            vendor_id=data.get("vendor_id"),
            invoice_number=data.get("invoice_number"),
            due_date=data.get("due_date"),
            raw_text=data.get("raw_text"),
            confidence=data.get("confidence", {}),
            line_items=data.get("line_items", []),
            approval_chain=data.get("approval_chain", []),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            approved_at=data.get("approved_at"),
            paid_at=data.get("paid_at")
        )
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            InvoiceStatus.DRAFT: [InvoiceStatus.SUBMITTED, InvoiceStatus.CANCELLED],
            InvoiceStatus.SUBMITTED: [InvoiceStatus.PENDING_APPROVAL, InvoiceStatus.APPROVED, InvoiceStatus.REJECTED, InvoiceStatus.CANCELLED],
            InvoiceStatus.PENDING_APPROVAL: [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED, InvoiceStatus.SUBMITTED],
            InvoiceStatus.APPROVED: [InvoiceStatus.PAID, InvoiceStatus.CANCELLED],
            InvoiceStatus.REJECTED: [InvoiceStatus.SUBMITTED, InvoiceStatus.CANCELLED],
            InvoiceStatus.PAID: [],  # Terminal state
            InvoiceStatus.CANCELLED: []  # Terminal state
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def is_editable(self) -> bool:
        """Check if invoice can be edited."""
        return self.status in [InvoiceStatus.DRAFT, InvoiceStatus.SUBMITTED, InvoiceStatus.REJECTED]
    
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
            "approver_id": approver_id,
            "status": status,
            "comments": comments,
            "timestamp": datetime.utcnow()
        }
        self.approval_chain.append(approval)
        self.updated_at = datetime.utcnow()
    
    def get_pending_approvers(self) -> List[str]:
        """Get list of approver IDs who haven't acted yet."""
        acted_approvers = {a["approver_id"] for a in self.approval_chain}
        # This would be populated from approval rules - for now return empty
        return []
    
    def has_approver_acted(self, approver_id: str) -> bool:
        """Check if a specific approver has already acted."""
        return any(a["approver_id"] == approver_id for a in self.approval_chain)
