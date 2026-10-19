"""
Purchase Order Matching Service.
Performs 2-way and 3-way matching between Supplier Invoices, Purchase Orders,
and Goods Receipts, detecting price, quantity, and total variance exceptions within tolerances.
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from utils.money import to_decimal, to_float
from logger_config import logger


class POMatchingService:
    """Matches supplier invoices against Purchase Orders and evaluates tolerances."""

    def __init__(self, db):
        self.db = db
        self.po_collection = db["purchase_orders"] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        if self.po_collection is not None:
            try:
                self.po_collection.create_index([("po_number", 1)], unique=True)
                self.po_collection.create_index([("vendor_name", 1)])
                self.po_collection.create_index([("status", 1)])
            except Exception as e:
                logger.error(f"Error ensuring PO indexes: {e}")

    def create_purchase_order(
        self,
        po_number: str,
        vendor_name: str,
        total_amount: float,
        line_items: List[Dict[str, Any]],
        vendor_id: Optional[str] = None,
        currency: str = "USD",
        tolerance_percent: float = 5.0,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[PurchaseOrder], Optional[str]]:
        if self.po_collection is None:
            return False, None, "Database not available"

        clean_po = po_number.strip().upper()
        if self.po_collection.find_one({"po_number": clean_po}):
            return False, None, f"Purchase Order '{clean_po}' already exists"

        po = PurchaseOrder(
            po_number=clean_po,
            vendor_name=vendor_name,
            total_amount=total_amount,
            line_items=line_items,
            vendor_id=vendor_id,
            currency=currency,
            tolerance_percent=tolerance_percent,
            notes=notes
        )

        res = self.po_collection.insert_one(po.to_dict())
        po._id = str(res.inserted_id)
        return True, po, None

    def get_po(self, po_number: str) -> Optional[PurchaseOrder]:
        if self.po_collection is None:
            return None
        doc = self.po_collection.find_one({"po_number": po_number.strip().upper()})
        return PurchaseOrder.from_dict(doc) if doc else None

    def match_invoice(
        self,
        invoice_data: Dict[str, Any],
        po_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match invoice against PO.
        Non-PO invoices cleanly return status 'no_po_required'.
        Returns detailed matching diagnostics, discrepancy exceptions, and tolerance results.
        """
        target_po_number = po_number or invoice_data.get("purchase_order_number")
        if not target_po_number:
            return {
                "matched": True,
                "has_po": False,
                "match_status": "no_po_required",
                "discrepancies": [],
                "details": "Non-PO invoice; routed to standard approval workflow"
            }

        target_po_number = target_po_number.strip().upper()
        po = self.get_po(target_po_number)

        if not po:
            return {
                "matched": False,
                "has_po": True,
                "po_number": target_po_number,
                "match_status": "missing_po",
                "discrepancies": [f"Purchase order '{target_po_number}' does not exist in procurement records"],
                "details": "Invoice references an invalid or missing Purchase Order"
            }

        if po.status in [PurchaseOrderStatus.CLOSED, PurchaseOrderStatus.CANCELLED]:
            return {
                "matched": False,
                "has_po": True,
                "po_number": target_po_number,
                "match_status": "closed_po",
                "discrepancies": [f"Purchase order '{target_po_number}' is already {po.status}"],
                "details": f"Cannot match invoice against a {po.status} PO"
            }

        discrepancies: List[str] = []

        # 1. Compare Currencies
        inv_curr = (invoice_data.get("currency") or "USD").upper()
        if inv_curr != po.currency.upper():
            discrepancies.append(f"Currency mismatch: Invoice is in {inv_curr}, PO is in {po.currency}")

        # 2. Compare Total Amount against configured tolerance
        inv_total = to_decimal(invoice_data.get("total", 0.0))
        po_total = to_decimal(po.total_amount)
        tolerance_multiplier = Decimal(str(1 + (po.tolerance_percent / 100.0)))
        max_allowed_total = (po_total * tolerance_multiplier).quantize(Decimal('0.01'))

        if inv_total > max_allowed_total:
            discrepancies.append(
                f"Invoice total ({inv_curr} {inv_total}) exceeds PO total ({po.currency} {po_total}) "
                f"beyond allowed tolerance of {po.tolerance_percent}% (max allowed: {max_allowed_total})"
            )

        # 3. Compare Line Items
        inv_items = invoice_data.get("line_items", [])
        po_items = po.line_items

        if inv_items and po_items:
            for inv_item in inv_items:
                inv_desc = inv_item.get("description", "").lower()
                inv_qty = float(inv_item.get("quantity", 1))
                inv_price = to_decimal(inv_item.get("unit_price", 0.0))

                # Find best matching PO item
                matched_po_item = None
                for p_item in po_items:
                    if p_item.get("description", "").lower() in inv_desc or inv_desc in p_item.get("description", "").lower():
                        matched_po_item = p_item
                        break

                if matched_po_item:
                    po_unit_price = to_decimal(matched_po_item.get("unit_price", 0.0))
                    # Unit price variance
                    if inv_price > po_unit_price:
                        discrepancies.append(
                            f"Price variance for '{matched_po_item.get('description')}': "
                            f"Invoiced unit price {inv_price} exceeds authorized PO price {po_unit_price}"
                        )

                    # Quantity variance: invoiced vs received
                    qty_received = float(matched_po_item.get("quantity_received", matched_po_item.get("quantity_ordered", 0)))
                    if inv_qty > qty_received:
                        discrepancies.append(
                            f"Quantity variance for '{matched_po_item.get('description')}': "
                            f"Invoiced quantity ({inv_qty}) exceeds goods received quantity ({qty_received})"
                        )

        is_matched = len(discrepancies) == 0

        return {
            "matched": is_matched,
            "has_po": True,
            "po_number": target_po_number,
            "match_status": "matched" if is_matched else "discrepancy_exception",
            "discrepancies": discrepancies,
            "po_total": po.total_amount,
            "invoice_total": to_float(inv_total),
            "tolerance_percent": po.tolerance_percent
        }
