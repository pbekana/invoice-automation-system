"""
Accounting Integration and Export Engine.
Handles General Ledger (GL) account mapping, tax category mapping,
balanced double-entry journal entry generation, export batch tracking,
and duplicate export prevention with idempotency controls.
"""

import io
import csv
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from bson import ObjectId  # type: ignore

from config import Config
from utils.money import to_decimal, to_float, CENT
from logger_config import logger


class GLAccounts:
    """Standard Chart of Accounts (COA) GL mapping."""
    CASH_AND_BANK = "1000"
    ACCOUNTS_RECEIVABLE = "1100"
    ACCOUNTS_PAYABLE = "2000"
    INPUT_TAX_RECEIVABLE = "2200"
    OUTPUT_TAX_PAYABLE = "2210"
    REVENUE_SALES = "4000"
    EXPENSE_SOFTWARE = "6100"
    EXPENSE_OFFICE_SUPPLIES = "6200"
    EXPENSE_TRAVEL_TRANSPORT = "6300"
    EXPENSE_MEALS_ENTERTAINMENT = "6400"
    EXPENSE_GENERAL_ADMIN = "6500"

    CATEGORY_MAP = {
        "software": EXPENSE_SOFTWARE,
        "supplies": EXPENSE_OFFICE_SUPPLIES,
        "transport": EXPENSE_TRAVEL_TRANSPORT,
        "travel": EXPENSE_TRAVEL_TRANSPORT,
        "food": EXPENSE_MEALS_ENTERTAINMENT,
        "meals": EXPENSE_MEALS_ENTERTAINMENT,
        "general": EXPENSE_GENERAL_ADMIN,
    }

    @classmethod
    def get_expense_account(cls, category: Optional[str]) -> str:
        if not category:
            return cls.EXPENSE_GENERAL_ADMIN
        cat_lower = category.lower().strip()
        for key, account in cls.CATEGORY_MAP.items():
            if key in cat_lower:
                return account
        return cls.EXPENSE_GENERAL_ADMIN


class AccountingExportService:
    """Manages GL mappings, balanced double-entry accounting exports, and batch reconciliation."""

    def __init__(self, db):
        self.db = db
        self.exports_collection = db["accounting_exports"] if db is not None else None
        self.invoices_collection = db[Config.INVOICES_COLLECTION] if db is not None else None
        self.payments_collection = db["payments"] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        if self.exports_collection is not None:
            try:
                self.exports_collection.create_index([("batch_id", 1)], unique=True)
                self.exports_collection.create_index([("created_at", -1)])
                self.exports_collection.create_index([("status", 1)])
            except Exception as e:
                logger.error(f"Error ensuring accounting export indexes: {e}")

    def export_approved_invoices_batch(
        self,
        user_id: str,
        invoice_ids: Optional[List[str]] = None,
        include_already_exported: bool = False
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Generate balanced double-entry journal entries for approved/paid AP invoices.
        Prevents duplicate export unless explicitly requested.
        Returns (success, batch_metadata, csv_content, error_message).
        """
        if self.invoices_collection is None or self.exports_collection is None:
            return False, None, None, "Database not available"

        try:
            query: Dict[str, Any] = {
                "status": {"$in": ["approved", "paid", "partially_paid"]}
            }

            if not include_already_exported:
                query["exported_to_accounting"] = {"$ne": True}

            if invoice_ids:
                query["_id"] = {"$in": [ObjectId(i) for i in invoice_ids]}

            invoices = list(self.invoices_collection.find(query).sort("date", 1))
            if not invoices:
                return False, None, None, "No unexported approved invoices found matching criteria"

            batch_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
            journal_entries = []
            total_debits = Decimal('0.00')
            total_credits = Decimal('0.00')

            csv_output = io.StringIO()
            fieldnames = [
                "Entry ID", "Posting Date", "Account Code", "Account Name",
                "Description", "Debit", "Credit", "Currency",
                "Entity Reference", "Invoice ID", "External Doc Number"
            ]
            writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
            writer.writeheader()

            exported_invoice_ids = []

            for inv in invoices:
                inv_id = str(inv["_id"])
                inv_num = inv.get("invoice_number") or inv_id
                company = inv.get("company") or "Unknown Vendor"
                date_str = inv.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
                currency = inv.get("currency") or "USD"

                tot = to_decimal(inv.get("total", 0.0))
                tax = to_decimal(inv.get("tax_amount", 0.0))
                disc = to_decimal(inv.get("discount", 0.0))
                subtotal = to_decimal(inv.get("subtotal", tot - tax + disc))

                expense_acc = GLAccounts.get_expense_account(inv.get("category"))

                # 1. Debit Expense
                net_expense = (subtotal - disc).quantize(CENT)
                writer.writerow({
                    "Entry ID": f"{batch_id}-{inv_id[:6]}-1",
                    "Posting Date": date_str,
                    "Account Code": expense_acc,
                    "Account Name": f"Operating Expense - {inv.get('category', 'General')}",
                    "Description": f"Bill from {company} (Inv #{inv_num})",
                    "Debit": f"{net_expense:.2f}",
                    "Credit": "0.00",
                    "Currency": currency,
                    "Entity Reference": company,
                    "Invoice ID": inv_id,
                    "External Doc Number": inv_num
                })
                total_debits += net_expense

                # 2. Debit Input Tax (if applicable)
                if tax > Decimal('0.00'):
                    writer.writerow({
                        "Entry ID": f"{batch_id}-{inv_id[:6]}-2",
                        "Posting Date": date_str,
                        "Account Code": GLAccounts.INPUT_TAX_RECEIVABLE,
                        "Account Name": "Input Tax / VAT Receivable",
                        "Description": f"Input Tax on Inv #{inv_num} from {company}",
                        "Debit": f"{tax:.2f}",
                        "Credit": "0.00",
                        "Currency": currency,
                        "Entity Reference": company,
                        "Invoice ID": inv_id,
                        "External Doc Number": inv_num
                    })
                    total_debits += tax

                # 3. Credit Accounts Payable
                writer.writerow({
                    "Entry ID": f"{batch_id}-{inv_id[:6]}-3",
                    "Posting Date": date_str,
                    "Account Code": GLAccounts.ACCOUNTS_PAYABLE,
                    "Account Name": "Accounts Payable",
                    "Description": f"Liability recognized for {company} (Inv #{inv_num})",
                    "Debit": "0.00",
                    "Credit": f"{tot:.2f}",
                    "Currency": currency,
                    "Entity Reference": company,
                    "Invoice ID": inv_id,
                    "External Doc Number": inv_num
                })
                total_credits += tot

                exported_invoice_ids.append(ObjectId(inv["_id"]))

            # Verify balance
            balance_diff = abs(total_debits - total_credits)
            if balance_diff > Decimal('0.05'):
                logger.error(f"Unbalanced journal entry in batch {batch_id}: Debits {total_debits} != Credits {total_credits}")
                return False, None, None, f"Double-entry balance verification failed: Debits ({total_debits}) != Credits ({total_credits})"

            csv_text = csv_output.getvalue()
            batch_hash = hashlib.sha256(csv_text.encode('utf-8')).hexdigest()

            # Record Batch in database
            now = datetime.utcnow()
            batch_record = {
                "batch_id": batch_id,
                "exported_by": user_id,
                "export_type": "ap_invoices",
                "invoice_count": len(invoices),
                "total_debits": to_float(total_debits),
                "total_credits": to_float(total_credits),
                "status": "completed",
                "checksum": batch_hash,
                "invoice_ids": [str(i) for i in exported_invoice_ids],
                "created_at": now
            }
            self.exports_collection.insert_one(batch_record)

            # Mark invoices as exported to prevent accidental duplicates
            self.invoices_collection.update_many(
                {"_id": {"$in": exported_invoice_ids}},
                {"$set": {
                    "exported_to_accounting": True,
                    "accounting_batch_id": batch_id,
                    "exported_at": now
                }}
            )

            logger.info(f"Accounting export batch {batch_id} generated successfully: {len(invoices)} invoices, balance verified.")
            return True, batch_record, csv_text, None

        except Exception as e:
            logger.error(f"Accounting export batch failed: {e}", exc_info=True)
            return False, None, None, f"Export failed: {str(e)}"

    def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List historical accounting exports with metadata and checksums."""
        if self.exports_collection is None:
            return []
        try:
            docs = list(self.exports_collection.find({}).sort("created_at", -1).limit(limit))
            for d in docs:
                d["_id"] = str(d["_id"])
                if "created_at" in d and hasattr(d["created_at"], "isoformat"):
                    d["created_at"] = d["created_at"].isoformat()
            return docs
        except Exception as e:
            logger.error(f"Error fetching accounting export history: {e}")
            return []
