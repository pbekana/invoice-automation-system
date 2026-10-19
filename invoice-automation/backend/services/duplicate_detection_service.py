"""
Multi-signal Duplicate Detection Service for Invoices.
Identifies definite and possible duplicates using document fingerprints,
normalized invoice numbers, vendor identities, amounts, and date proximities.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from config import Config
from logger_config import logger
from utils.money import to_decimal, to_float
from bson import ObjectId  # type: ignore


class DuplicateMatchLevel:
    DEFINITE = "definite_duplicate"
    POSSIBLE = "possible_duplicate"
    NONE = "none"


class DuplicateDetectionService:
    """Detects and manages potential duplicate invoices across multiple business signals."""

    def __init__(self, db):
        self.db = db
        self.invoices_collection = db[Config.INVOICES_COLLECTION] if db is not None else None

    @staticmethod
    def normalize_invoice_number(num_str: Optional[str]) -> str:
        """
        Normalize invoice numbers for robust matching.
        Strips common prefixes, non-alphanumerics, and leading zeros from numeric components:
        'INV-00042'     -> '42'
        '#00123-A'      -> '123A'
        'inv/2026/0009' -> '20269'
        '0000'          -> '0'
        """
        if not num_str:
            return ""
        s = str(num_str).strip()
        # Remove common prefixes like 'INV-', 'INVOICE:', 'NO.', '#'
        s = re.sub(r'^(?:INV(?:OICE)?|BILL|RECEIPT|NO)[\s\-_/#.:]*', '', s, flags=re.IGNORECASE)
        s = re.sub(r'^[#\s\-_/.:]+', '', s)

        # Split into alphanumeric chunks by any non-alphanumeric separator
        parts = re.split(r'[^A-Za-z0-9]+', s)
        normalized_parts = []
        for p in parts:
            if not p:
                continue
            if p.isdigit():
                p_norm = p.lstrip('0')
                normalized_parts.append(p_norm if p_norm else '0')
            else:
                m = re.match(r'^(0+)(\d*[A-Za-z].*)$', p)
                if m:
                    p = m.group(2)
                normalized_parts.append(p.upper())

        result = "".join(normalized_parts)
        if not result and s:
            return "0"
        return result

    def check_invoice(
        self,
        invoice_number: Optional[str],
        vendor_id: Optional[str],
        company: Optional[str],
        total: float,
        date_str: Optional[str],
        currency: str = "USD",
        sha256_hash: Optional[str] = None,
        tenant_id: Optional[str] = None,
        exclude_invoice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run multi-signal duplicate checks.
        Returns detailed duplicate diagnostic result.
        """
        if self.invoices_collection is None:
            return {"match_level": DuplicateMatchLevel.NONE, "matches": []}

        matches: List[Dict[str, Any]] = []
        normalized_num = self.normalize_invoice_number(invoice_number)
        total_dec = to_decimal(total)

        base_query: Dict[str, Any] = {
            "status": {"$nin": ["cancelled", "rejected"]}
        }
        if tenant_id:
            base_query["tenant_id"] = tenant_id
        if exclude_invoice_id:
            try:
                base_query["_id"] = {"$ne": ObjectId(exclude_invoice_id)}
            except Exception:
                pass

        # ---------------------------------------------------------
        # Signal 1: Document SHA-256 Fingerprint (Definite Duplicate)
        # ---------------------------------------------------------
        if sha256_hash:
            fingerprint_query = {**base_query, "sha256_hash": sha256_hash}
            matched_doc = self.invoices_collection.find_one(fingerprint_query)
            if matched_doc:
                matches.append({
                    "invoice_id": str(matched_doc["_id"]),
                    "invoice_number": matched_doc.get("invoice_number"),
                    "company": matched_doc.get("company"),
                    "total": matched_doc.get("total"),
                    "date": matched_doc.get("date"),
                    "reason": "Exact document binary fingerprint match (identical uploaded file)",
                    "match_level": DuplicateMatchLevel.DEFINITE,
                    "confidence": 1.0
                })

        # ---------------------------------------------------------
        # Signal 2: Vendor + Normalized Invoice Number (Definite Duplicate)
        # ---------------------------------------------------------
        if normalized_num and (vendor_id or company):
            vendor_criteria: Dict[str, Any] = {}
            if vendor_id:
                vendor_criteria["vendor_id"] = vendor_id
            elif company:
                vendor_criteria["company"] = {"$regex": f"^{re.escape(company)}$", "$options": "i"}

            candidate_invoices = list(self.invoices_collection.find({**base_query, **vendor_criteria}))
            for cand in candidate_invoices:
                cand_norm = cand.get("normalized_invoice_number") or self.normalize_invoice_number(cand.get("invoice_number"))
                if cand_norm and cand_norm == normalized_num:
                    if not any(m["invoice_id"] == str(cand["_id"]) for m in matches):
                        matches.append({
                            "invoice_id": str(cand["_id"]),
                            "invoice_number": cand.get("invoice_number"),
                            "company": cand.get("company"),
                            "total": cand.get("total"),
                            "date": cand.get("date"),
                            "reason": f"Normalized invoice number '{normalized_num}' match for same vendor",
                            "match_level": DuplicateMatchLevel.DEFINITE,
                            "confidence": 0.98
                        })

        # ---------------------------------------------------------
        # Signal 3: Vendor + Total + Date proximity + Currency (Possible Duplicate)
        # ---------------------------------------------------------
        if (vendor_id or company) and total_dec > 0 and date_str:
            fuzzy_query = {
                **base_query,
                "total": to_float(total_dec),
                "currency": currency
            }
            if vendor_id:
                fuzzy_query["vendor_id"] = vendor_id
            elif company:
                fuzzy_query["company"] = {"$regex": f"^{re.escape(company)}$", "$options": "i"}

            fuzzy_matches = list(self.invoices_collection.find(fuzzy_query))
            for cand in fuzzy_matches:
                if any(m["invoice_id"] == str(cand["_id"]) for m in matches):
                    continue
                cand_date = cand.get("date")
                # Compare exact date or within +/- 3 days
                is_date_close = False
                if cand_date == date_str:
                    is_date_close = True
                elif cand_date and date_str:
                    try:
                        d1 = datetime.strptime(date_str, "%Y-%m-%d")
                        d2 = datetime.strptime(cand_date, "%Y-%m-%d")
                        if abs((d1 - d2).days) <= 3:
                            is_date_close = True
                    except Exception:
                        pass

                if is_date_close:
                    matches.append({
                        "invoice_id": str(cand["_id"]),
                        "invoice_number": cand.get("invoice_number"),
                        "company": cand.get("company"),
                        "total": cand.get("total"),
                        "date": cand_date,
                        "reason": f"Identical vendor, amount ({currency} {total:.2f}), and date proximity ({cand_date})",
                        "match_level": DuplicateMatchLevel.POSSIBLE,
                        "confidence": 0.85
                    })

        # Determine overall match level
        if any(m["match_level"] == DuplicateMatchLevel.DEFINITE for m in matches):
            overall_level = DuplicateMatchLevel.DEFINITE
        elif any(m["match_level"] == DuplicateMatchLevel.POSSIBLE for m in matches):
            overall_level = DuplicateMatchLevel.POSSIBLE
        else:
            overall_level = DuplicateMatchLevel.NONE

        return {
            "match_level": overall_level,
            "has_duplicate": overall_level != DuplicateMatchLevel.NONE,
            "matches": matches,
            "normalized_invoice_number": normalized_num
        }

    def resolve_duplicate_investigation(
        self,
        invoice_id: str,
        user_id: str,
        resolution: str,
        investigation_notes: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Record duplicate investigation outcome.
        Resolution can be:
        - 'confirmed_duplicate': marks invoice as duplicate and cancels it.
        - 'cleared_false_positive': clears duplicate hold and permits approval/payment.
        """
        if self.invoices_collection is None:
            return False, "Database not available"

        if resolution not in ["confirmed_duplicate", "cleared_false_positive"]:
            return False, "Invalid resolution. Must be 'confirmed_duplicate' or 'cleared_false_positive'"

        if not investigation_notes or not investigation_notes.strip():
            return False, "Investigation notes are required"

        try:
            update_fields: Dict[str, Any] = {
                "duplicate_investigation": {
                    "investigated_by": user_id,
                    "investigated_at": datetime.utcnow(),
                    "resolution": resolution,
                    "notes": investigation_notes.strip()
                },
                "updated_at": datetime.utcnow()
            }

            if resolution == "confirmed_duplicate":
                update_fields["status"] = "cancelled"
                update_fields["cancelled_reason"] = f"Confirmed duplicate: {investigation_notes.strip()}"
            elif resolution == "cleared_false_positive":
                update_fields["duplicate_status"] = "cleared"

            res = self.invoices_collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": update_fields}
            )

            if res.matched_count == 0:
                return False, "Invoice not found"

            logger.info(f"Duplicate investigation resolved for invoice {invoice_id} as '{resolution}' by {user_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error resolving duplicate investigation: {e}")
            return False, f"Failed to record investigation: {str(e)}"
