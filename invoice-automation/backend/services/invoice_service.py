"""Invoice business logic service."""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from config import Config  # type: ignore
from models.invoice import Invoice, InvoiceStatus, ApprovalStatus  # type: ignore
from models.user import UserRole  # type: ignore
from logger_config import logger


class InvoiceService:
    """Handles invoice business logic and workflow."""
    
    def __init__(self, db):
        self.db = db
        self.invoices_collection = db[Config.INVOICES_COLLECTION] if db is not None else None
    
    def create_invoice(
        self,
        company: str,
        date: str,
        total: float,
        category: str,
        submitter_id: str,
        vendor_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        due_date: Optional[str] = None,
        raw_text: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[Invoice], Optional[str]]:
        """Create a new invoice."""
        if not self.invoices_collection:
            return False, None, "Database not available"
        
        try:
            invoice = Invoice(
                company=company,
                date=date,
                total=total,
                category=category,
                submitter_id=submitter_id,
                vendor_id=vendor_id,
                invoice_number=invoice_number,
                due_date=due_date,
                raw_text=raw_text,
                confidence=confidence,
                notes=notes,
                status=InvoiceStatus.SUBMITTED
            )
            
            result = self.invoices_collection.insert_one(invoice.to_dict())
            invoice._id = str(result.inserted_id)
            
            logger.info(f"Invoice created: {invoice._id} by user {submitter_id}")
            return True, invoice, None
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return False, None, "Failed to create invoice"
    
    def get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        if not self.invoices_collection:
            return None
        
        try:
            from bson import ObjectId  # type: ignore
            invoice_data = self.invoices_collection.find_one({"_id": ObjectId(invoice_id)})
            if invoice_data:
                return Invoice.from_dict(invoice_data)
        except Exception as e:
            logger.error(f"Error fetching invoice: {e}")
        
        return None
    
    def update_invoice(
        self,
        invoice_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Update invoice fields."""
        if not self.invoices_collection:
            return False, "Database not available"
        
        try:
            from bson import ObjectId  # type: ignore
            
            # Get current invoice
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, "Invoice not found"
            
            # Check if invoice is editable
            if not invoice.is_editable():
                return False, f"Cannot edit invoice in status: {invoice.status}"
            
            # Protect certain fields
            protected = ["_id", "submitter_id", "created_at", "approval_chain"]
            for field in protected:
                updates.pop(field, None)
            
            # Update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = self.invoices_collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Invoice not found"
            
            logger.info(f"Invoice updated: {invoice_id} by user {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error updating invoice: {e}")
            return False, "Failed to update invoice"
    
    def change_status(
        self,
        invoice_id: str,
        new_status: str,
        user_id: str,
        comments: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Change invoice status (with validation)."""
        if not self.invoices_collection:
            return False, "Database not available"
        
        try:
            from bson import ObjectId  # type: ignore
            
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, "Invoice not found"
            
            # Validate transition
            if not invoice.can_transition_to(new_status):
                return False, f"Cannot transition from {invoice.status} to {new_status}"
            
            updates = {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
            
            # Set timestamps for certain statuses
            if new_status == InvoiceStatus.APPROVED:
                updates["approved_at"] = datetime.utcnow()
            elif new_status == InvoiceStatus.PAID:
                updates["paid_at"] = datetime.utcnow()
            
            # Add to approval chain if comments provided
            if comments:
                invoice.add_approval(user_id, new_status, comments)
                updates["approval_chain"] = invoice.approval_chain
            
            result = self.invoices_collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Invoice not found"
            
            logger.info(f"Invoice status changed: {invoice_id} from {invoice.status} to {new_status} by {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error changing invoice status: {e}")
            return False, "Failed to change status"
    
    def submit_for_approval(
        self,
        invoice_id: str,
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Submit invoice for approval."""
        return self.change_status(
            invoice_id,
            InvoiceStatus.PENDING_APPROVAL,
            user_id,
            "Submitted for approval"
        )
    
    def approve_invoice(
        self,
        invoice_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Approve an invoice."""
        if not self.invoices_collection:
            return False, "Database not available"
        
        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"
        
        # Check if already acted
        if invoice.has_approver_acted(approver_id):
            return False, "You have already acted on this invoice"
        
        # Change status
        return self.change_status(
            invoice_id,
            InvoiceStatus.APPROVED,
            approver_id,
            comments or "Approved"
        )
    
    def reject_invoice(
        self,
        invoice_id: str,
        approver_id: str,
        reason: str
    ) -> Tuple[bool, Optional[str]]:
        """Reject an invoice."""
        if not reason or not reason.strip():
            return False, "Rejection reason is required"
        
        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"
        
        # Check if already acted
        if invoice.has_approver_acted(approver_id):
            return False, "You have already acted on this invoice"
        
        return self.change_status(
            invoice_id,
            InvoiceStatus.REJECTED,
            approver_id,
            f"Rejected: {reason}"
        )
    
    def mark_as_paid(
        self,
        invoice_id: str,
        user_id: str,
        payment_reference: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Mark invoice as paid."""
        comments = f"Marked as paid. Reference: {payment_reference}" if payment_reference else "Marked as paid"
        return self.change_status(invoice_id, InvoiceStatus.PAID, user_id, comments)
    
    def cancel_invoice(
        self,
        invoice_id: str,
        user_id: str,
        reason: str
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an invoice."""
        if not reason or not reason.strip():
            return False, "Cancellation reason is required"
        
        return self.change_status(
            invoice_id,
            InvoiceStatus.CANCELLED,
            user_id,
            f"Cancelled: {reason}"
        )
    
    def list_invoices(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        submitter_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        user_roles: Optional[List[str]] = None
    ) -> List[Invoice]:
        """List invoices with filtering."""
        if not self.invoices_collection:
            return []
        
        try:
            query = {}
            
            # If not admin, only show user's own invoices
            if user_roles and UserRole.ADMIN not in user_roles:
                query["submitter_id"] = user_id
            
            if status:
                query["status"] = status
            
            if submitter_id:
                query["submitter_id"] = submitter_id
            
            if vendor_id:
                query["vendor_id"] = vendor_id
            
            if category:
                query["category"] = category
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                if date_query:
                    query["date"] = date_query
            
            invoices_data = self.invoices_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            return [Invoice.from_dict(inv) for inv in invoices_data]
            
        except Exception as e:
            logger.error(f"Error listing invoices: {e}")
            return []
    
    def count_invoices(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count invoices matching query."""
        if not self.invoices_collection:
            return 0
        
        try:
            return self.invoices_collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"Error counting invoices: {e}")
            return 0
    
    def get_pending_approvals(self, approver_id: str) -> List[Invoice]:
        """Get invoices pending approval from specific approver."""
        # For now, return all pending invoices
        # In future, this would check approval_rules and routing
        return self.list_invoices(status=InvoiceStatus.PENDING_APPROVAL)
    
    def check_duplicate(
        self,
        invoice_number: Optional[str],
        vendor_id: Optional[str],
        total: float,
        date: str
    ) -> Optional[Invoice]:
        """Check for potential duplicate invoices."""
        if not self.invoices_collection or not invoice_number:
            return None
        
        try:
            # Look for invoices with same invoice number and vendor
            query = {
                "invoice_number": invoice_number,
                "status": {"$nin": [InvoiceStatus.CANCELLED, InvoiceStatus.REJECTED]}
            }
            
            if vendor_id:
                query["vendor_id"] = vendor_id
            
            duplicate_data = self.invoices_collection.find_one(query)
            if duplicate_data:
                return Invoice.from_dict(duplicate_data)
            
            # Also check for same vendor, amount, and date (fuzzy duplicate)
            if vendor_id:
                fuzzy_query = {
                    "vendor_id": vendor_id,
                    "total": total,
                    "date": date,
                    "status": {"$nin": [InvoiceStatus.CANCELLED, InvoiceStatus.REJECTED]}
                }
                duplicate_data = self.invoices_collection.find_one(fuzzy_query)
                if duplicate_data:
                    return Invoice.from_dict(duplicate_data)
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
        
        return None


# Singleton instance (will be initialized in app.py)
invoice_service = None
