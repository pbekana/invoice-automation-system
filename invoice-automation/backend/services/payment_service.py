"""
Authoritative Payment Recording Service for Accounts Payable and Accounts Receivable.
Calculates balances dynamically using Decimal precision, supports full/partial payments,
enforces idempotency, handles reversals, and guarantees financial consistency.
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal
from bson import ObjectId  # type: ignore

from config import Config
from models.payment import Payment, PaymentStatus, PaymentMethod
from models.invoice import InvoiceStatus
from utils.money import to_decimal, to_float, CENT
from logger_config import logger


class PaymentService:
    """Handles financial payment transactions, balance reconciliation, and reversals."""

    def __init__(self, db):
        self.db = db
        self.payments_collection = db["payments"] if db is not None else None
        self.ap_collection = db[Config.INVOICES_COLLECTION] if db is not None else None
        self.ar_collection = db["ar_invoices"] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        if self.payments_collection is not None:
            try:
                self.payments_collection.create_index([("invoice_id", 1)])
                self.payments_collection.create_index(
                    [("idempotency_key", 1)],
                    unique=True,
                    partialFilterExpression={"idempotency_key": {"$type": "string"}}
                )
                self.payments_collection.create_index([("status", 1)])
                self.payments_collection.create_index([("created_at", -1)])
            except Exception as e:
                logger.error(f"Error ensuring payment indexes: {e}")

    def get_invoice_balance(self, invoice_id: str, invoice_type: str = "payable") -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate authoritative (total_amount, total_paid, outstanding_balance) using Decimal arithmetic.
        """
        col = self.ap_collection if invoice_type == "payable" else self.ar_collection
        if col is None or self.payments_collection is None:
            return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')

        try:
            inv = col.find_one({"_id": ObjectId(invoice_id)})
            if not inv:
                return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')

            total_amount = to_decimal(inv.get("total", 0.0))

            # Query all completed payments for this invoice
            completed_payments = list(self.payments_collection.find({
                "invoice_id": str(invoice_id),
                "status": PaymentStatus.COMPLETED
            }))

            total_paid = sum((to_decimal(p.get("amount", 0.0)) for p in completed_payments), Decimal('0.00'))
            outstanding_balance = max(Decimal('0.00'), total_amount - total_paid)

            return total_amount, total_paid, outstanding_balance

        except Exception as e:
            logger.error(f"Error calculating invoice balance for {invoice_id}: {e}")
            return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        user_id: str,
        payment_date: Optional[str] = None,
        payment_method: str = PaymentMethod.BANK_TRANSFER,
        transaction_reference: Optional[str] = None,
        external_reference: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        notes: Optional[str] = None,
        invoice_type: str = "payable"
    ) -> Tuple[bool, Optional[Payment], Optional[float], Optional[str]]:
        """
        Record a full or partial payment against an invoice.
        Returns (success, payment_obj, remaining_balance, error_message).
        """
        if self.payments_collection is None or self.db is None:
            return False, None, None, "Database not available"

        # 1. Idempotency Check
        if idempotency_key:
            existing_payment = self.payments_collection.find_one({"idempotency_key": idempotency_key})
            if existing_payment:
                logger.info(f"Idempotent payment match returned for key: {idempotency_key}")
                _, _, bal = self.get_invoice_balance(invoice_id, invoice_type)
                return True, Payment.from_dict(existing_payment), to_float(bal), None

        # 2. Validate Invoice Exists & Workflow State
        col = self.ap_collection if invoice_type == "payable" else self.ar_collection
        if col is None:
            return False, None, None, "Invoice collection unavailable"

        try:
            inv = col.find_one({"_id": ObjectId(invoice_id)})
            if not inv:
                return False, None, None, f"{invoice_type.title()} invoice not found"

            current_status = inv.get("status")

            if invoice_type == "payable":
                # AP Business Rule: Invoices must be APPROVED or PARTIALLY_PAID before payments can be applied!
                if current_status not in [InvoiceStatus.APPROVED, "partially_paid"]:
                    return False, None, None, f"Cannot record payment on AP invoice in '{current_status}' status. Invoice must be approved first."
            else:
                # AR Business Rule: Invoices must be sent or partially_paid
                if current_status in ["draft", "cancelled"]:
                    return False, None, None, f"Cannot record payment on AR invoice in '{current_status}' status."

            # 3. Calculate Authoritative Balance
            payment_dec = to_decimal(amount)
            if payment_dec <= Decimal('0.00'):
                return False, None, None, "Payment amount must be strictly greater than 0"

            total_amount, total_paid, outstanding_balance = self.get_invoice_balance(invoice_id, invoice_type)

            if outstanding_balance <= Decimal('0.00'):
                return False, None, None, "Invoice is already fully paid"

            # Allow minor rounding penny tolerance if user pays within 1 cent of balance
            if payment_dec > outstanding_balance:
                diff = payment_dec - outstanding_balance
                if diff <= Decimal('0.02'):
                    payment_dec = outstanding_balance
                else:
                    return False, None, None, f"Payment amount ({payment_dec}) exceeds outstanding balance ({outstanding_balance})"

            # 4. Construct Payment Record
            actual_date = payment_date or datetime.utcnow().strftime("%Y-%m-%d")
            currency = inv.get("currency", "USD")

            payment = Payment(
                invoice_id=invoice_id,
                amount=to_float(payment_dec),
                payment_date=actual_date,
                created_by=user_id,
                invoice_type=invoice_type,
                currency=currency,
                payment_method=payment_method,
                transaction_reference=transaction_reference,
                external_reference=external_reference,
                status=PaymentStatus.COMPLETED,
                idempotency_key=idempotency_key,
                notes=notes
            )

            # Insert payment
            insert_result = self.payments_collection.insert_one(payment.to_dict())
            payment._id = str(insert_result.inserted_id)

            # 5. Atomically update invoice status and balance
            new_total_paid = total_paid + payment_dec
            new_balance = max(Decimal('0.00'), total_amount - new_total_paid)

            new_status = InvoiceStatus.PAID if new_balance == Decimal('0.00') else "partially_paid"
            now = datetime.utcnow()

            invoice_updates: Dict[str, Any] = {
                "status": new_status,
                "paid_amount": to_float(new_total_paid),
                "outstanding_balance": to_float(new_balance),
                "updated_at": now
            }
            if new_status == InvoiceStatus.PAID:
                invoice_updates["paid_at"] = now

            col.update_one({"_id": ObjectId(invoice_id)}, {"$set": invoice_updates})

            logger.info(
                f"Recorded payment of {currency} {payment.amount} for {invoice_type} invoice {invoice_id}. "
                f"New status: {new_status}, Remaining balance: {new_balance}"
            )

            return True, payment, to_float(new_balance), None

        except Exception as e:
            logger.error(f"Error processing payment for invoice {invoice_id}: {e}", exc_info=True)
            return False, None, None, f"Failed to record payment: {str(e)}"

    def reverse_payment(
        self,
        payment_id: str,
        user_id: str,
        reason: Optional[str] = None,
        reversal_reason: Optional[str] = None,
        invoice_type: Optional[str] = None
    ) -> Tuple[bool, Optional[Payment], Optional[float], Optional[str]]:
        """
        Reverse a previously completed payment through a controlled operation.
        Restores the invoice outstanding balance and updates workflow status.
        """
        actual_reason = reversal_reason or reason
        if self.payments_collection is None:
            return False, None, None, "Database not available"

        if not actual_reason or not actual_reason.strip():
            return False, None, None, "Reversal reason is mandatory"

        try:
            payment_doc = self.payments_collection.find_one({"_id": ObjectId(payment_id)})
            if not payment_doc:
                return False, None, None, "Payment transaction not found"

            if payment_doc.get("status") != PaymentStatus.COMPLETED:
                return False, None, None, f"Cannot reverse payment in '{payment_doc.get('status')}' status"

            invoice_id = payment_doc["invoice_id"]
            actual_invoice_type = invoice_type or payment_doc.get("invoice_type", "payable")
            col = self.ap_collection if actual_invoice_type == "payable" else self.ar_collection

            # 1. Update Payment status to REVERSED
            now = datetime.utcnow()
            self.payments_collection.update_one(
                {"_id": ObjectId(payment_id)},
                {"$set": {
                    "status": PaymentStatus.REVERSED,
                    "reversed_at": now,
                    "reversed_by": user_id,
                    "reversal_reason": actual_reason.strip()
                }}
            )

            # 2. Recalculate invoice balance
            total_amount, total_paid, outstanding_balance = self.get_invoice_balance(invoice_id, actual_invoice_type)

            # Determine restored status
            if outstanding_balance >= total_amount:
                restored_status = InvoiceStatus.APPROVED if actual_invoice_type == "payable" else "sent"
            else:
                restored_status = "partially_paid"

            if col is not None:
                col.update_one(
                    {"_id": ObjectId(invoice_id)},
                    {"$set": {
                        "status": restored_status,
                        "paid_amount": to_float(total_paid),
                        "outstanding_balance": to_float(outstanding_balance),
                        "updated_at": now
                    }}
                )

            updated_payment_doc = self.payments_collection.find_one({"_id": ObjectId(payment_id)})
            payment_obj = Payment.from_dict(updated_payment_doc) if updated_payment_doc else None

            logger.info(f"Payment {payment_id} reversed by {user_id}. Invoice {invoice_id} status restored to {restored_status}")
            return True, payment_obj, to_float(outstanding_balance), None

        except Exception as e:
            logger.error(f"Error reversing payment {payment_id}: {e}", exc_info=True)
            return False, None, None, f"Failed to reverse payment: {str(e)}"

    def get_payment_history(self, invoice_id: str) -> Dict[str, Any]:
        """Get complete payment history and ledger for an invoice."""
        if self.payments_collection is None:
            return {"payments": [], "total_paid": 0.0, "outstanding_balance": 0.0}

        try:
            docs = list(self.payments_collection.find({"invoice_id": str(invoice_id)}).sort("created_at", -1))
            payments = [Payment.from_dict(d).to_json() for d in docs]

            total_amount, total_paid, outstanding_balance = self.get_invoice_balance(invoice_id)

            return {
                "payments": payments,
                "total_amount": to_float(total_amount),
                "total_paid": to_float(total_paid),
                "outstanding_balance": to_float(outstanding_balance),
                "payment_count": len([p for p in payments if p["status"] == PaymentStatus.COMPLETED])
            }
        except Exception as e:
            logger.error(f"Error getting payment history for {invoice_id}: {e}")
            return {"payments": [], "total_paid": 0.0, "outstanding_balance": 0.0}
