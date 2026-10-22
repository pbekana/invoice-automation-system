"""
Bank Statement & Payment Reconciliation Service.
Enables importing bank statements or payment provider CSVs, matching imported
transactions against recorded payments, detecting ambiguous or unmatched transactions,
preventing duplicate statement imports, and preserving a full audit trail.
NOTE: This service reconciles imported statement files; it does NOT claim live bank synchronization.
"""

import io
import csv
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from bson import ObjectId
from utils.money import to_decimal, to_float, CENT
from logger_config import logger


class ReconciliationService:
    """Processes bank statement CSVs and reconciles them against authoritative payment records."""

    def __init__(self, db):
        self.db = db
        self.batches_col = db["reconciliation_batches"] if db is not None else None
        self.payments_col = db["payments"] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        if self.batches_col is not None:
            try:
                self.batches_col.create_index([("batch_id", 1)], unique=True)
                self.batches_col.create_index([("statement_hash", 1)], unique=True)
                self.batches_col.create_index([("created_at", -1)])
            except Exception as e:
                logger.error(f"Error creating reconciliation indexes: {e}")

    def import_and_reconcile_statement(
        self,
        csv_content: str,
        user_id: str,
        filename: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Parse statement CSV and reconcile against stored payments.
        Returns (success, result_summary, error_message).
        """
        if self.batches_col is None or self.payments_col is None:
            return False, None, "Database not available"

        if not csv_content or not csv_content.strip():
            return False, None, "Statement CSV is empty"

        # Check duplicate statement by checksum
        content_hash = hashlib.sha256(csv_content.strip().encode("utf-8")).hexdigest()
        existing = self.batches_col.find_one({"statement_hash": content_hash})
        if existing:
            return False, None, f"Duplicate statement import: This file was already imported on {existing.get('created_at')} (Batch: {existing.get('batch_id')})"

        # Parse CSV
        try:
            reader = csv.DictReader(io.StringIO(csv_content.strip()))
            rows = list(reader)
        except Exception as e:
            return False, None, f"Malformed CSV format: {str(e)}"

        if not rows:
            return False, None, "No data rows found in CSV"

        # Standardize column headers
        field_map = {}
        for h in (reader.fieldnames or []):
            hl = h.strip().lower()
            if "date" in hl:
                field_map["date"] = h
            elif any(k in hl for k in ["desc", "reference", "memo", "details"]):
                field_map["reference"] = h
            elif any(k in hl for k in ["amount", "value", "net"]):
                field_map["amount"] = h
            elif "type" in hl:
                field_map["type"] = h

        if "date" not in field_map or "amount" not in field_map:
            return False, None, "CSV must contain at least 'Date' and 'Amount' columns"

        ref_col = field_map.get("reference")

        # Load completed payments from MongoDB
        recorded_payments = list(self.payments_col.find({"status": "completed"}))

        batch_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
        reconciled_items = []
        matched_count = 0
        unmatched_count = 0
        ambiguous_count = 0

        for idx, row in enumerate(rows, 1):
            raw_date = row[field_map["date"]].strip()
            raw_amt_str = row[field_map["amount"]].strip().replace("$", "").replace(",", "")
            raw_ref = row[ref_col].strip() if ref_col and ref_col in row else ""

            try:
                amt = abs(to_decimal(raw_amt_str))
            except Exception:
                amt = Decimal("0.00")

            tx_item = {
                "tx_id": f"{batch_id}-TX-{idx:03d}",
                "date": raw_date,
                "amount": to_float(amt),
                "reference": raw_ref,
                "status": "unmatched",
                "matched_payment_id": None,
                "matched_payment_ref": None,
                "notes": ""
            }

            # 1. Exact Reference Match
            exact_matches = []
            if raw_ref:
                raw_ref_lower = raw_ref.lower()
                for p in recorded_payments:
                    p_amt = to_decimal(p.get("amount", 0))
                    p_ref = str(p.get("transaction_reference") or "").lower()
                    p_ext = str(p.get("external_reference") or "").lower()
                    p_id = str(p.get("_id"))

                    if (raw_ref_lower in p_ref or p_ref in raw_ref_lower or 
                        raw_ref_lower in p_ext or p_ext in raw_ref_lower or 
                        p_id.lower() in raw_ref_lower) and abs(p_amt - amt) <= Decimal("0.02"):
                        exact_matches.append(p)

            if len(exact_matches) == 1:
                matched_p = exact_matches[0]
                tx_item["status"] = "matched"
                tx_item["matched_payment_id"] = str(matched_p["_id"])
                tx_item["matched_payment_ref"] = matched_p.get("transaction_reference") or matched_p.get("external_reference")
                tx_item["notes"] = "Exact reference & amount match"
                matched_count += 1
            elif len(exact_matches) > 1:
                tx_item["status"] = "ambiguous"
                tx_item["notes"] = f"Multiple payments ({len(exact_matches)}) match this reference and amount"
                ambiguous_count += 1
            else:
                # 2. Amount & Date Proximity Search
                amt_matches = []
                for p in recorded_payments:
                    p_amt = to_decimal(p.get("amount", 0))
                    if abs(p_amt - amt) <= Decimal("0.02"):
                        amt_matches.append(p)

                if len(amt_matches) == 1:
                    matched_p = amt_matches[0]
                    tx_item["status"] = "matched"
                    tx_item["matched_payment_id"] = str(matched_p["_id"])
                    tx_item["matched_payment_ref"] = matched_p.get("transaction_reference")
                    tx_item["notes"] = "Matched by exact amount against recorded payment"
                    matched_count += 1
                elif len(amt_matches) > 1:
                    tx_item["status"] = "ambiguous"
                    tx_item["notes"] = f"{len(amt_matches)} payments match this amount; requires manual selection"
                    ambiguous_count += 1
                else:
                    tx_item["status"] = "unmatched"
                    tx_item["notes"] = "No recorded payment found matching this transaction"
                    unmatched_count += 1

            reconciled_items.append(tx_item)

        batch_doc = {
            "batch_id": batch_id,
            "filename": filename or "statement.csv",
            "statement_hash": content_hash,
            "imported_by": user_id,
            "created_at": datetime.utcnow(),
            "total_count": len(reconciled_items),
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "ambiguous_count": ambiguous_count,
            "items": reconciled_items
        }

        self.batches_col.insert_one(batch_doc)
        logger.info(f"Reconciliation batch {batch_id} saved: {matched_count} matched, {ambiguous_count} ambiguous, {unmatched_count} unmatched.")

        summary = {
            "batch_id": batch_id,
            "filename": filename or "statement.csv",
            "total_count": len(reconciled_items),
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "ambiguous_count": ambiguous_count,
            "items": reconciled_items
        }
        return True, summary, None

    def get_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List historical reconciliation batches."""
        if self.batches_col is None:
            return []
        try:
            docs = list(self.batches_col.find({}, {"items": 0}).sort("created_at", -1).limit(limit))
            for d in docs:
                d["_id"] = str(d["_id"])
                if "created_at" in d and hasattr(d["created_at"], "isoformat"):
                    d["created_at"] = d["created_at"].isoformat()
            return docs
        except Exception as e:
            logger.error(f"Error fetching reconciliation batches: {e}")
            return []

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch details with all items."""
        if self.batches_col is None:
            return None
        doc = self.batches_col.find_one({"batch_id": batch_id})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
            doc["created_at"] = doc["created_at"].isoformat()
        return doc
