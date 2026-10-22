"""Invoice business logic service."""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from bson import ObjectId  # type: ignore

from config import Config  # type: ignore
from models.invoice import Invoice, InvoiceStatus, ApprovalStatus  # type: ignore
from models.user import UserRole  # type: ignore
from services.duplicate_detection_service import DuplicateDetectionService  # type: ignore
from utils.money import to_decimal, to_float
from logger_config import logger


class InvoiceService:
    """Handles invoice business logic, atomic state machine transitions, and workflow."""

    def __init__(self, db, audit_service=None):
        self.db = db
        self.invoices_collection = db[Config.INVOICES_COLLECTION] if db is not None else None
        self.duplicate_service = DuplicateDetectionService(db)
        self.audit_service = audit_service

    def create_invoice(
        self,
        company: str,
        date: Optional[str],
        total: float,
        category: str,
        submitter_id: str,
        vendor_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        due_date: Optional[str] = None,
        currency: str = "USD",
        subtotal: Optional[float] = None,
        tax_amount: float = 0.0,
        tax_rate: float = 0.0,
        discount: float = 0.0,
        line_items: Optional[List[Dict[str, Any]]] = None,
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
        notes: Optional[str] = None,
        status: str = InvoiceStatus.SUBMITTED
    ) -> Tuple[bool, Optional[Invoice], Optional[str]]:
        """Create a new invoice with structured fields and financial validation metadata."""
        if self.invoices_collection is None:
            return False, None, "Database not available"

        try:
            invoice = Invoice(
                company=company,
                date=date,
                total=total,
                category=category,
                submitter_id=submitter_id,
                status=status,
                vendor_id=vendor_id,
                invoice_number=invoice_number,
                due_date=due_date,
                currency=currency,
                subtotal=subtotal,
                tax_amount=tax_amount,
                tax_rate=tax_rate,
                discount=discount,
                line_items=line_items,
                payment_terms=payment_terms,
                purchase_order_number=purchase_order_number,
                po_match_status=po_match_status,
                duplicate_status=duplicate_status,
                sha256_hash=sha256_hash,
                storage_key=storage_key,
                original_filename=original_filename,
                validation=validation,
                raw_text=raw_text,
                confidence=confidence,
                notes=notes
            )

            now = invoice.created_at or datetime.utcnow()
            initial_history = {
                "invoice_id": None,
                "previous_status": None,
                "new_status": invoice.status,
                "user_id": str(submitter_id) if submitter_id else None,
                "role": "submitter",
                "timestamp": now,
                "reason": "Initial submission" if invoice.status == InvoiceStatus.SUBMITTED else "Invoice created",
                "comment": "Initial submission" if invoice.status == InvoiceStatus.SUBMITTED else "Invoice created"
            }
            invoice.status_history = [initial_history]

            inv_dict = invoice.to_dict()
            if invoice_number:
                inv_dict["normalized_invoice_number"] = DuplicateDetectionService.normalize_invoice_number(invoice_number)

            result = self.invoices_collection.insert_one(inv_dict)
            invoice._id = str(result.inserted_id)
            initial_history["invoice_id"] = invoice._id
            self.invoices_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status_history.0.invoice_id": invoice._id}}
            )

            if getattr(self, 'audit_service', None):
                self.audit_service.log(
                    action=AuditAction.INVOICE_CREATED,
                    entity_type="invoice",
                    entity_id=invoice._id,
                    user_id=str(submitter_id) if submitter_id else None,
                    details={
                        "previous_status": None,
                        "new_status": invoice.status,
                        "role": "submitter",
                        "reason": "Invoice created"
                    },
                    new_values={"status": invoice.status, "total": invoice.total, "company": invoice.company}
                )

            logger.info(f"Invoice created: {invoice._id} by user {submitter_id}")
            return True, invoice, None

        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return False, None, f"Failed to create invoice: {str(e)}"

    def get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        if self.invoices_collection is None:
            return None

        try:
            invoice_data = self.invoices_collection.find_one({"_id": ObjectId(invoice_id)})
            if invoice_data:
                return Invoice.from_dict(invoice_data)
        except Exception as e:
            logger.error(f"Error fetching invoice {invoice_id}: {e}")

        return None

    def update_invoice(
        self,
        invoice_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Update invoice fields with validation."""
        if self.invoices_collection is None:
            return False, "Database not available"

        try:
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, "Invoice not found"

            # Check if invoice is editable
            if not invoice.is_editable():
                return False, f"Cannot edit invoice in status: {invoice.status}"

            # Protect critical workflow fields
            protected = ["_id", "submitter_id", "created_at", "approval_chain", "status_history", "status", "storage_key", "sha256_hash"]
            for field in protected:
                updates.pop(field, None)

            # If invoice number is updated, recalculate normalized invoice number
            if "invoice_number" in updates:
                updates["normalized_invoice_number"] = DuplicateDetectionService.normalize_invoice_number(updates["invoice_number"])

            # If totals/financials are updated, quantize them
            if "total" in updates:
                updates["total"] = to_float(updates["total"])
                # Also update outstanding balance if no payments have been made yet
                if invoice.paid_amount == 0.0:
                    updates["outstanding_balance"] = updates["total"]

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
        comments: Optional[str] = None,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Change invoice status with server-side state machine validation,
        persistent status history tracking, and optimistic concurrency control.
        """
        if self.invoices_collection is None:
            return False, "Database not available"

        try:
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, "Invoice not found"

            # Validate state machine transition
            if not invoice.can_transition_to(new_status):
                return False, f"Invalid transition: Cannot transition from '{invoice.status}' to '{new_status}'"

            previous_status = invoice.status
            now = datetime.utcnow()

            updates: Dict[str, Any] = {
                "status": new_status,
                "updated_at": now
            }

            if new_status == InvoiceStatus.APPROVED:
                updates["approved_at"] = now
            elif new_status == InvoiceStatus.PAID:
                updates["paid_at"] = now

            # Record in approval chain
            if comments or new_status in [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED]:
                invoice.add_approval(user_id, new_status, comments)
                updates["approval_chain"] = invoice.approval_chain

            # Construct status history record
            history_record = {
                "invoice_id": str(invoice_id),
                "previous_status": previous_status,
                "new_status": new_status,
                "user_id": str(user_id) if user_id else None,
                "role": role or "user",
                "user_name": user_info.get("name") if user_info else None,
                "user_email": user_info.get("email") if user_info else None,
                "timestamp": now,
                "reason": comments or "",
                "comment": comments or ""
            }

            # Atomic update enforcing optimistic concurrency check on status and recording history
            result = self.invoices_collection.update_one(
                {"_id": ObjectId(invoice_id), "status": previous_status},
                {
                    "$set": updates,
                    "$push": {"status_history": history_record}
                }
            )

            if result.matched_count == 0:
                return False, "Concurrent conflict: Invoice was modified or transitioned by another user"

            # Persist to audit_logs collection consistently
            if getattr(self, 'audit_service', None):
                action = f"invoice_{new_status}"
                self.audit_service.log(
                    action=action,
                    entity_type="invoice",
                    entity_id=str(invoice_id),
                    user_id=str(user_id) if user_id else None,
                    details={
                        "previous_status": previous_status,
                        "new_status": new_status,
                        "role": role or "user",
                        "reason": comments or "",
                        "comments": comments or "",
                        "user_name": user_info.get("name") if user_info else None,
                        "user_email": user_info.get("email") if user_info else None
                    },
                    changes={"status": {"from": previous_status, "to": new_status}},
                    previous_values={"status": previous_status},
                    new_values={"status": new_status}
                )

            logger.info(f"Invoice status changed: {invoice_id} from {previous_status} to {new_status} by {user_id} ({role})")
            return True, None

        except Exception as e:
            logger.error(f"Error changing invoice status: {e}")
            return False, "Failed to change status"

    def submit_for_approval(
        self,
        invoice_id: str,
        user_id: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Submit invoice for approval."""
        return self.change_status(
            invoice_id,
            InvoiceStatus.PENDING_APPROVAL,
            user_id,
            "Submitted for approval",
            role=role or "submitter",
            user_info=user_info
        )

    def submit_invoice(
        self,
        invoice_id: str,
        user_id: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Submit invoice alias for workflow approval."""
        return self.submit_for_approval(invoice_id, user_id, role=role, user_info=user_info)

    def approve_invoice(
        self,
        invoice_id: str,
        approver_id: str,
        comments: Optional[str] = None,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Approve an invoice.
        Enforces segregation of duties: submitter cannot approve their own invoice.
        """
        if self.invoices_collection is None:
            return False, "Database not available"

        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"

        # 1. Enforce Segregation of Duties
        if invoice.submitter_id and str(invoice.submitter_id) == str(approver_id):
            logger.warning(f"Self-approval rejected for user {approver_id} on invoice {invoice_id}")
            return False, "Segregation of duties violation: Submitter cannot approve their own invoice"

        # 2. Check if already acted
        if invoice.has_approver_acted(approver_id):
            return False, "You have already acted on this invoice"

        # 3. Check for unresolved duplicate hold
        if invoice.duplicate_status == "flagged_duplicate":
            return False, "Cannot approve invoice with unresolved duplicate flag. Please complete duplicate investigation first."

        # Change status
        return self.change_status(
            invoice_id,
            InvoiceStatus.APPROVED,
            approver_id,
            comments or "Approved",
            role=role or "approver",
            user_info=user_info
        )

    def request_revision(
        self,
        invoice_id: str,
        approver_id: str,
        reason: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Request revision/correction on an invoice with feedback for submitter."""
        if not reason or not reason.strip():
            return False, "Revision notes / feedback are required"

        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"

        if invoice.has_approver_acted(approver_id):
            return False, "You have already acted on this invoice"

        return self.change_status(
            invoice_id,
            InvoiceStatus.NEEDS_REVISION,
            approver_id,
            f"Needs Revision: {reason.strip()}",
            role=role or "approver",
            user_info=user_info
        )

    def reject_invoice(
        self,
        invoice_id: str,
        approver_id: str,
        reason: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Reject an invoice with mandatory reason."""
        if not reason or not reason.strip():
            return False, "Rejection reason is required"

        invoice = self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False, "Invoice not found"

        if invoice.has_approver_acted(approver_id):
            return False, "You have already acted on this invoice"

        return self.change_status(
            invoice_id,
            InvoiceStatus.REJECTED,
            approver_id,
            f"Rejected: {reason.strip()}",
            role=role or "approver",
            user_info=user_info
        )

    def mark_as_paid(
        self,
        invoice_id: str,
        user_id: str,
        payment_reference: Optional[str] = None,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Mark invoice as paid."""
        comments = f"Marked as paid. Reference: {payment_reference}" if payment_reference else "Marked as paid"
        return self.change_status(
            invoice_id,
            InvoiceStatus.PAID,
            user_id,
            comments,
            role=role or "finance",
            user_info=user_info
        )

    def cancel_invoice(
        self,
        invoice_id: str,
        user_id: str,
        reason: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an invoice."""
        if not reason or not reason.strip():
            return False, "Cancellation reason is required"

        return self.change_status(
            invoice_id,
            InvoiceStatus.CANCELLED,
            user_id,
            f"Cancelled: {reason.strip()}",
            role=role or "submitter",
            user_info=user_info
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
        user_roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None
    ) -> List[Invoice]:
        """List invoices with filtering, pagination, and role-based data isolation."""
        if self.invoices_collection is None:
            return []

        try:
            query: Dict[str, Any] = {}

            if tenant_id:
                query["tenant_id"] = tenant_id

            # Role-based scoping: submitters only see their own submitted invoices.
            # Admins, approvers, finance users, and viewers can see invoices across the organization.
            org_view_roles = {UserRole.ADMIN, UserRole.APPROVER, UserRole.FINANCE, "finance_user", UserRole.VIEWER}
            if user_roles and not any(r in org_view_roles for r in user_roles):
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
                date_query: Dict[str, Any] = {}
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
        if self.invoices_collection is None:
            return 0
        try:
            return self.invoices_collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"Error counting invoices: {e}")
            return 0

    def get_pending_approvals(self, approver_id: str) -> List[Invoice]:
        """
        Get invoices pending approval from specific approver.
        Excludes invoices submitted by the approver themselves (segregation of duties).
        """
        if self.invoices_collection is None:
            return []
        try:
            query = {
                "status": InvoiceStatus.PENDING_APPROVAL,
                "submitter_id": {"$ne": str(approver_id)}  # Submitter cannot approve their own
            }
            docs = self.invoices_collection.find(query).sort("created_at", -1)
            return [Invoice.from_dict(d) for d in docs]
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return []

    def check_duplicate(
        self,
        invoice_number: Optional[str],
        vendor_id: Optional[str],
        total: float,
        date: str,
        company: Optional[str] = None,
        sha256_hash: Optional[str] = None,
        exclude_invoice_id: Optional[str] = None
    ) -> Optional[Invoice]:
        """Check for potential duplicate invoices using multi-signal detection."""
        diag = self.duplicate_service.check_invoice(
            invoice_number=invoice_number,
            vendor_id=vendor_id,
            company=company,
            total=total,
            date_str=date,
            sha256_hash=sha256_hash,
            exclude_invoice_id=exclude_invoice_id
        )
        if diag.get("has_duplicate") and diag.get("matches"):
            first_match_id = diag["matches"][0]["invoice_id"]
            return self.get_invoice_by_id(first_match_id)
        return None


invoice_service = None
