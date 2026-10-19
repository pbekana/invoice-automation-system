"""
Accounts Receivable (AR) Service.
Manages customer billing, line item math using Decimal precision,
aging schedules (current, 1-30, 31-60, 61-90, 90+ days), credit notes,
and customer statements.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from bson import ObjectId  # type: ignore

from models.credit_note import CreditNote
from utils.money import to_decimal, to_float, calculate_line_item_total, CENT
from logger_config import logger


class ARService:
    """Handles Accounts Receivable lifecycle, aging analysis, and statements."""

    def __init__(self, db):
        self.db = db
        self.ar_collection = db["ar_invoices"] if db is not None else None
        self.credit_notes_collection = db["credit_notes"] if db is not None else None
        self.customers_collection = db["customers"] if db is not None else None
        self.payments_collection = db["payments"] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        if self.ar_collection is not None:
            try:
                self.ar_collection.create_index([("invoice_number", 1)], unique=True)
                self.ar_collection.create_index([("customer_id", 1)])
                self.ar_collection.create_index([("status", 1)])
                self.ar_collection.create_index([("due_date", 1)])
            except Exception as e:
                logger.error(f"Error ensuring AR indexes: {e}")

    def calculate_invoice_totals(
        self,
        line_items: List[Dict[str, Any]],
        discount_val: float = 0.0
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Compute authoritative (subtotal, tax_amount, discount, total) with Decimal precision.
        """
        subtotal = Decimal('0.00')
        tax_total = Decimal('0.00')

        for item in line_items:
            qty = Decimal(str(item.get("quantity", 1)))
            unit_price = to_decimal(item.get("unit_price", 0.0))
            tax_rate = Decimal(str(item.get("tax_rate", 0.0)))

            line_sub = (qty * unit_price).quantize(CENT)
            line_tax = (line_sub * (tax_rate / Decimal('100.0'))).quantize(CENT)

            subtotal += line_sub
            tax_total += line_tax

        discount = to_decimal(discount_val)
        total = max(Decimal('0.00'), subtotal + tax_total - discount)

        return subtotal, tax_total, discount, total

    def apply_credit_note(
        self,
        invoice_id: str,
        amount: float,
        reason: str,
        user_id: str
    ) -> Tuple[bool, Optional[CreditNote], Optional[float], Optional[str]]:
        """
        Apply a credit note against an AR invoice.
        Reduces outstanding balance and marks invoice as credited if balance reaches zero.
        """
        if self.ar_collection is None or self.credit_notes_collection is None:
            return False, None, None, "Database not available"

        try:
            inv = self.ar_collection.find_one({"_id": ObjectId(invoice_id)})
            if not inv:
                return False, None, None, "AR invoice not found"

            current_balance = to_decimal(inv.get("outstanding_balance", inv.get("total", 0.0)))
            credit_amount = to_decimal(amount)

            if credit_amount <= Decimal('0.00'):
                return False, None, None, "Credit amount must be greater than zero"

            if credit_amount > current_balance:
                return False, None, None, f"Credit amount ({credit_amount}) cannot exceed outstanding balance ({current_balance})"

            # Generate credit note number
            cn_count = self.credit_notes_collection.count_documents({}) + 1
            cn_number = f"CN-{datetime.utcnow().year}-{cn_count:04d}"

            credit_note = CreditNote(
                credit_note_number=cn_number,
                invoice_id=invoice_id,
                customer_id=inv["customer_id"],
                amount=to_float(credit_amount),
                reason=reason,
                created_by=user_id,
                currency=inv.get("currency", "USD")
            )

            res = self.credit_notes_collection.insert_one(credit_note.to_dict())
            credit_note._id = str(res.inserted_id)

            # Reduce outstanding balance
            new_balance = max(Decimal('0.00'), current_balance - credit_amount)
            new_status = "credited" if new_balance == Decimal('0.00') else inv.get("status", "sent")

            self.ar_collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": {
                    "outstanding_balance": to_float(new_balance),
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }}
            )

            logger.info(f"Credit note {cn_number} applied for {credit_amount} on invoice {invoice_id}. Remaining: {new_balance}")
            return True, credit_note, to_float(new_balance), None

        except Exception as e:
            logger.error(f"Error applying credit note to {invoice_id}: {e}", exc_info=True)
            return False, None, None, f"Failed to apply credit note: {str(e)}"

    def get_receivables_aging_report(self, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate authoritative Accounts Receivable aging report.
        Categories:
        - Current (not yet due)
        - 1-30 days overdue
        - 31-60 days overdue
        - 61-90 days overdue
        - 90+ days overdue
        Calculated using actual outstanding balance.
        """
        if self.ar_collection is None:
            return {"aging_buckets": {}, "customers": [], "total_outstanding": 0.0}

        try:
            ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else datetime.utcnow().date()

            # Query all active unpaid AR invoices
            query = {
                "type": "receivable",
                "status": {"$nin": ["paid", "draft", "cancelled", "credited"]}
            }

            invoices = list(self.ar_collection.find(query))

            buckets = {
                "current": Decimal('0.00'),
                "days_1_30": Decimal('0.00'),
                "days_31_60": Decimal('0.00'),
                "days_61_90": Decimal('0.00'),
                "days_90_plus": Decimal('0.00'),
            }

            customer_aging: Dict[str, Dict[str, Any]] = {}
            grand_outstanding = Decimal('0.00')

            for inv in invoices:
                # Outstanding balance
                balance = to_decimal(inv.get("outstanding_balance", inv.get("total", 0.0)))
                if balance <= Decimal('0.00'):
                    continue

                cust_id = str(inv.get("customer_id"))
                cust_name = inv.get("customer_name") or "Unknown Customer"

                if cust_id not in customer_aging:
                    customer_aging[cust_id] = {
                        "customer_id": cust_id,
                        "customer_name": cust_name,
                        "current": 0.0,
                        "days_1_30": 0.0,
                        "days_31_60": 0.0,
                        "days_61_90": 0.0,
                        "days_90_plus": 0.0,
                        "total_outstanding": 0.0
                    }

                # Calculate days overdue
                due_date_str = inv.get("due_date")
                bucket_key = "current"

                if due_date_str:
                    try:
                        due_d = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        days_overdue = (ref_date - due_d).days
                        if days_overdue <= 0:
                            bucket_key = "current"
                        elif 1 <= days_overdue <= 30:
                            bucket_key = "days_1_30"
                        elif 31 <= days_overdue <= 60:
                            bucket_key = "days_31_60"
                        elif 61 <= days_overdue <= 90:
                            bucket_key = "days_61_90"
                        else:
                            bucket_key = "days_90_plus"
                    except Exception:
                        bucket_key = "current"

                buckets[bucket_key] += balance
                customer_aging[cust_id][bucket_key] = to_float(to_decimal(customer_aging[cust_id][bucket_key]) + balance)
                customer_aging[cust_id]["total_outstanding"] = to_float(to_decimal(customer_aging[cust_id]["total_outstanding"]) + balance)
                grand_outstanding += balance

            return {
                "as_of_date": ref_date.strftime("%Y-%m-%d"),
                "total_outstanding": to_float(grand_outstanding),
                "aging_buckets": {k: to_float(v) for k, v in buckets.items()},
                "customers": list(customer_aging.values())
            }

        except Exception as e:
            logger.error(f"Error compiling AR aging report: {e}", exc_info=True)
            return {"aging_buckets": {}, "customers": [], "total_outstanding": 0.0, "error": str(e)}

    def get_customer_statement(self, customer_id: str) -> Dict[str, Any]:
        """Compile complete activity statement for a customer."""
        if self.ar_collection is None:
            return {"customer": None, "invoices": [], "credit_notes": [], "net_balance": 0.0}

        try:
            cust = self.customers_collection.find_one({"_id": ObjectId(customer_id)}) if self.customers_collection is not None else None
            invoices = list(self.ar_collection.find({"customer_id": customer_id}).sort("issue_date", 1))

            c_notes = list(self.credit_notes_collection.find({"customer_id": customer_id})) if self.credit_notes_collection is not None else []

            serialized_invoices = []
            net_balance = Decimal('0.00')

            for inv in invoices:
                inv["id"] = str(inv.pop("_id"))
                bal = to_decimal(inv.get("outstanding_balance", inv.get("total", 0.0)))
                net_balance += bal
                serialized_invoices.append(inv)

            return {
                "customer": {
                    "id": str(cust["_id"]),
                    "name": cust["name"],
                    "email": cust.get("email"),
                    "phone": cust.get("phone")
                } if cust else {"id": customer_id, "name": "Unknown"},
                "invoices": serialized_invoices,
                "credit_notes": [{**cn, "_id": str(cn["_id"])} for cn in c_notes],
                "net_outstanding_balance": to_float(net_balance)
            }
        except Exception as e:
            logger.error(f"Error compiling customer statement for {customer_id}: {e}")
            return {"customer": None, "invoices": [], "credit_notes": [], "net_balance": 0.0}
