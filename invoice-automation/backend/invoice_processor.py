"""
Structured Invoice Processing and OCR Extraction Service.
Supports PDF (native text and scanned raster) and images.
Extracts structured invoice metadata, currency, dates, line items, PO numbers,
computes field confidence, and separates document extraction from financial validation.
"""

import re
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

try:
    import cv2  # pyre-ignore[21]
    import numpy as np  # pyre-ignore[21]
    import pytesseract  # pyre-ignore[21]
    try:
        import fitz  # PyMuPDF type: ignore
        HAS_FITZ = True
    except ImportError:
        HAS_FITZ = False
    from pdf2image import convert_from_path  # pyre-ignore[21]
    from dateutil import parser  # type: ignore
    from config import Config  # pyre-ignore[21]
    from logger_config import logger
    from utils.money import to_decimal, to_float, calculate_line_item_total, verify_financial_equation
    HAS_OCR_DEPS = True
except ImportError as e:
    HAS_OCR_DEPS = False
    HAS_FITZ = False
    from utils.money import to_decimal, to_float, calculate_line_item_total, verify_financial_equation
    from dateutil import parser  # type: ignore


class InvoiceProcessor:
    """Service to handle document text extraction, structured parsing, and financial validation."""

    CURRENCY_SYMBOLS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        'ETB': 'ETB',
        'USD': 'USD',
        'EUR': 'EUR',
        'GBP': 'GBP',
        'CAD': 'CAD',
        'AUD': 'AUD',
        'CHF': 'CHF',
    }

    def __init__(self):
        self.has_ocr_deps = HAS_OCR_DEPS

    def extract_text(self, filepath: str) -> str:
        """
        Extract raw text using PyMuPDF direct text extraction with fallback to OCR.
        Never uses hardcoded mock values.
        """
        if not os.path.exists(filepath):
            return f"[Error: File not found: {filepath}]"

        ext = os.path.splitext(filepath)[1].lower()
        if not self.has_ocr_deps:
            return f"[OCR Dependencies missing — cannot process {ext}]"

        try:
            if ext == ".pdf":
                return self._process_pdf(filepath)
            elif ext.lstrip(".") in Config.ALLOWED_EXTENSIONS:
                return self._process_image(filepath)
            else:
                return f"[Unsupported file type: {ext}]"
        except Exception as e:
            return f"[Extraction Error: {str(e)}]"

    def extract_fields(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse raw text into structured invoice metadata with field confidences
        and separate financial validation results.
        """
        if not raw_text or raw_text.startswith("["):
            return {
                "company": "Unknown",
                "invoice_number": None,
                "date": None,
                "due_date": None,
                "currency": "USD",
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "tax_rate": 0.0,
                "discount": 0.0,
                "total": 0.0,
                "payment_terms": None,
                "purchase_order_number": None,
                "line_items": [],
                "confidence": {"overall": 0.0},
                "raw_text": raw_text or "",
                "validation": {
                    "is_valid": False,
                    "requires_review": True,
                    "errors": ["Failed to extract text from document"],
                    "warnings": []
                }
            }

        company, company_conf = self._extract_company_with_conf(raw_text)
        invoice_number, inv_num_conf = self._extract_invoice_number(raw_text)
        date, date_conf = self._extract_date_with_conf(raw_text)
        due_date = self._extract_due_date(raw_text)
        currency, curr_conf = self._extract_currency(raw_text)
        total, total_conf = self._extract_total_with_conf(raw_text)
        subtotal, subtotal_conf = self._extract_subtotal(raw_text, total)
        tax_amount, tax_rate = self._extract_tax(raw_text)
        discount = self._extract_discount(raw_text)
        po_number = self._extract_po_number(raw_text)
        payment_terms = self._extract_payment_terms(raw_text)
        line_items = self._extract_line_items(raw_text)

        confidence = {
            "company": company_conf,
            "invoice_number": inv_num_conf,
            "date": date_conf,
            "total": total_conf,
            "currency": curr_conf,
            "overall": round(
                (company_conf + inv_num_conf + date_conf + total_conf + curr_conf) / 5.0,
                2
            )
        }

        extracted = {
            "company": company,
            "invoice_number": invoice_number,
            "date": date,
            "due_date": due_date,
            "currency": currency,
            "subtotal": to_float(subtotal),
            "tax_amount": to_float(tax_amount),
            "tax_rate": float(tax_rate),
            "discount": to_float(discount),
            "total": to_float(total),
            "payment_terms": payment_terms,
            "purchase_order_number": po_number,
            "line_items": line_items,
            "confidence": confidence,
            "raw_text": raw_text
        }

        # Perform separated financial validation
        validation = self.validate_extracted_data(extracted)
        extracted["validation"] = validation

        return extracted

    def validate_extracted_data(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform authoritative validation of extracted invoice data.
        Validates required fields, date formats, line item totals, and subtotal/tax consistency.
        """
        errors: List[str] = []
        warnings: List[str] = []
        requires_review = False

        # 1. Required Fields Validation
        if not fields.get("company") or fields.get("company") == "Unknown Company":
            warnings.append("Company / Vendor name could not be reliably identified")
            requires_review = True

        if not fields.get("invoice_number"):
            warnings.append("Invoice number is missing")
            requires_review = True

        if not fields.get("date"):
            errors.append("Invoice date is missing or invalid")
            requires_review = True

        total_dec = to_decimal(fields.get("total", 0.0))
        if total_dec <= Decimal('0.00'):
            errors.append("Total amount must be greater than zero")
            requires_review = True

        # 2. Currency Validation
        if not fields.get("currency"):
            warnings.append("Currency not explicitly detected; defaulting to USD")
            requires_review = True

        # 3. Line Items Validation
        line_items = fields.get("line_items", [])
        if line_items:
            computed_items_subtotal = Decimal('0.00')
            for idx, item in enumerate(line_items, 1):
                qty = item.get("quantity", 1)
                unit_price = to_decimal(item.get("unit_price", 0.0))
                expected_total = calculate_line_item_total(qty, unit_price)
                stated_total = to_decimal(item.get("line_total", expected_total))

                if abs(expected_total - stated_total) > Decimal('0.02'):
                    warnings.append(
                        f"Line item {idx} ({item.get('description', '')}) total mismatch: "
                        f"{qty} x {unit_price} = {expected_total}, but stated is {stated_total}"
                    )
                    requires_review = True
                computed_items_subtotal += stated_total

            subtotal_dec = to_decimal(fields.get("subtotal", 0.0))
            if subtotal_dec > Decimal('0.00') and abs(computed_items_subtotal - subtotal_dec) > Decimal('0.05'):
                warnings.append(
                    f"Sum of line items ({computed_items_subtotal}) differs from stated subtotal ({subtotal_dec})"
                )
                requires_review = True

        # 4. Financial Equation Validation
        subtotal_val = to_decimal(fields.get("subtotal", 0.0))
        tax_val = to_decimal(fields.get("tax_amount", 0.0))
        disc_val = to_decimal(fields.get("discount", 0.0))

        if subtotal_val > Decimal('0.00'):
            consistent, expected_tot, msg = verify_financial_equation(
                subtotal=subtotal_val,
                tax_amount=tax_val,
                discount=disc_val,
                total=total_dec,
                tolerance=Decimal('0.05')
            )
            if not consistent:
                warnings.append(msg)
                requires_review = True

        # 5. Low confidence check
        overall_conf = fields.get("confidence", {}).get("overall", 1.0)
        if overall_conf < 0.65:
            warnings.append(f"Low overall extraction confidence ({int(overall_conf * 100)}%); manual review required")
            requires_review = True

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "requires_review": requires_review or not is_valid,
            "errors": errors,
            "warnings": warnings,
            "flags_for_review": list(set(errors + warnings))
        }

    # =========================================================================
    # INTERNAL OCR & TEXT EXTRACTION HELPERS
    # =========================================================================

    def _process_pdf(self, filepath: str) -> str:
        """Direct text extraction with PyMuPDF; fallback to OCR images if scanned."""
        text = ""
        if HAS_FITZ:
            try:
                doc = fitz.open(filepath)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                if len(text.strip()) > 50:
                    return text
            except Exception:
                pass

        # Fallback to OCR rasterization
        try:
            images = convert_from_path(filepath, dpi=Config.DPI)
            text_parts = [self._ocr_image(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)) for img in images]
            return "\n".join(text_parts)
        except Exception as e:
            return f"[PDF OCR Fallback Error: {str(e)}]"

    def _process_image(self, filepath: str) -> str:
        """Read image from path and perform OCR."""
        img = cv2.imread(filepath)
        if img is None:
            return "[Error: Could not read image file]"
        return self._ocr_image(img)

    def _preprocess_image(self, img):
        """Standard grayscale, denoising, adaptive thresholding."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return thresh

    def _ocr_image(self, img) -> str:
        """Apply pre-processing and Tesseract OCR."""
        try:
            processed = self._preprocess_image(img)
            return pytesseract.image_to_string(processed, config=f"--psm {Config.OCR_PSM}").strip()
        except Exception as e:
            return f"[OCR failure: {str(e)}]"

    # =========================================================================
    # FIELD EXTRACTION LOGIC
    # =========================================================================

    def _extract_company_with_conf(self, text: str) -> Tuple[str, float]:
        company = self._extract_company(text)
        if company != "Unknown Company":
            return company, 0.90
        return "Unknown Company", 0.30

    def _extract_company(self, text: str) -> str:
        """Find company name based on keywords and header position."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        keywords = ['inc', 'ltd', 'llc', 'corp', 'corporation', 'limited', 'services', 'stores', 'solutions', 'technologies']

        for line in lines[:8]:
            line_lower = line.lower()
            if any(k in line_lower for k in keywords):
                return line[:100]
            if re.match(r'^[A-Z][A-Za-z0-9\s&\.\-]+$', line):
                if not any(stop in line_lower for stop in ['invoice', 'date', 'bill to', 'ship to', 'statement', 'receipt', 'order #']):
                    if len(line) > 3:
                        return line[:100]

        return lines[0][:100] if lines else "Unknown Company"

    def _extract_invoice_number(self, text: str) -> Tuple[Optional[str], float]:
        """Extract invoice number using common patterns."""
        patterns = [
            r'(?:invoice\s*(?:#|no|number|num|id)?[:\s]*)([A-Za-z0-9\-_/]+)',
            r'(?:inv\s*(?:#|no)?[:\s]*)([A-Za-z0-9\-_/]+)',
            r'(?:bill\s*(?:#|no|number)?[:\s]*)([A-Za-z0-9\-_/]+)',
            r'(?:order\s*(?:#|no|number)?[:\s]*)([A-Za-z0-9\-_/]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if len(val) >= 2 and not val.lower() in ['date', 'to', 'for', 'due']:
                    return val, 0.92
        return None, 0.0

    def _extract_date_with_conf(self, text: str) -> Tuple[Optional[str], float]:
        date = self._extract_date(text)
        if date:
            return date, 0.90
        return None, 0.0

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract invoice date without silently inventing today's date if absent."""
        try:
            date_patterns = [
                r'(?:invoice\s*date|date|dated)[:\s]*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})',
                r'(?:invoice\s*date|date|dated)[:\s]*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{4})',
                r'(?:invoice\s*date|date|dated)[:\s]*([A-Za-z]+ \d{1,2},? \d{4})',
                r'(?:invoice\s*date|date|dated)[:\s]*(\d{1,2} [A-Za-z]+ \d{4})',
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parsed = parser.parse(match.group(1), fuzzy=True)
                    return parsed.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract payment due date."""
        try:
            patterns = [
                r'(?:due\s*date|payment\s*due)[:\s]*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})',
                r'(?:due\s*date|payment\s*due)[:\s]*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{4})',
                r'(?:due\s*date|payment\s*due)[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parsed = parser.parse(match.group(1), fuzzy=True)
                    return parsed.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None

    def _extract_currency(self, text: str) -> Tuple[str, float]:
        """Detect currency from symbols or 3-letter ISO codes."""
        # Check explicit symbols first
        for symbol, curr in self.CURRENCY_SYMBOLS.items():
            if symbol in text:
                return curr, 0.95
        # Search for ISO currency patterns
        iso_match = re.search(r'\b(USD|EUR|GBP|ETB|CAD|AUD|CHF|JPY)\b', text, re.IGNORECASE)
        if iso_match:
            return iso_match.group(1).upper(), 0.90
        return "USD", 0.50

    def _extract_total_with_conf(self, text: str) -> Tuple[float, float]:
        total = self._extract_total(text)
        if total > 0.0:
            return total, 0.92
        return 0.0, 0.10

    def _extract_total(self, text: str) -> float:
        """Extract final total using keywords and positioning."""
        text_lower = text.lower()
        keywords = ['grand total', 'amount due', 'amount payable', 'total due', 'total amount', 'balance due', 'total']

        best_total = 0.0

        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'[:\s]*[\$€£¥]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))'
            match = re.search(pattern, text_lower)
            if match:
                try:
                    val = float(match.group(1).replace(',', ''))
                    if val > best_total:
                        best_total = val
                except Exception:
                    continue

        if best_total == 0.0:
            amounts = re.findall(r'[\$€£¥]?\s*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2}|[0-9]+\.[0-9]{2})', text)
            processed = []
            for a in amounts:
                try:
                    processed.append(float(a.replace(',', '')))
                except Exception:
                    continue
            if processed:
                best_total = max(processed)

        return float(f"{best_total:.2f}")

    def _extract_subtotal(self, text: str, total: float) -> Tuple[float, float]:
        match = re.search(r'\bsubtotal[:\s]*[\$€£¥]?\s*([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
        if match:
            try:
                sub = float(match.group(1).replace(',', ''))
                return sub, 0.90
            except Exception:
                pass
        return total, 0.60

    def _extract_tax(self, text: str) -> Tuple[float, float]:
        """Extract tax amount and applicable tax rate percentage."""
        tax_amount = 0.0
        tax_rate = 0.0

        rate_match = re.search(r'(?:tax|vat|gst)[\s\(]*([0-9]+(?:\.[0-9]+)?)%', text, re.IGNORECASE)
        if rate_match:
            try:
                tax_rate = float(rate_match.group(1))
            except Exception:
                pass

        amt_match = re.search(r'\b(?:tax|vat|gst|sales tax)[:\s]*[\$€£¥]?\s*([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
        if amt_match:
            try:
                tax_amount = float(amt_match.group(1).replace(',', ''))
            except Exception:
                pass

        return tax_amount, tax_rate

    def _extract_discount(self, text: str) -> float:
        match = re.search(r'\bdiscount[:\s]*[\$€£¥]?\s*([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except Exception:
                pass
        return 0.0

    def _extract_po_number(self, text: str) -> Optional[str]:
        patterns = [
            r'\b(?:po|p\.o\.|purchase\s*order)\s*(?:#|no|number|num)?[:\s]*([A-Za-z0-9\-_]+)',
            r'\border\s*(?:#|no)[:\s]*([A-Za-z0-9\-_]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val.lower() not in ['date', 'terms']:
                    return val
        return None

    def _extract_payment_terms(self, text: str) -> Optional[str]:
        terms_patterns = [
            r'\b(net\s*(?:10|15|30|45|60|90))\b',
            r'\b(due\s*on\s*receipt)\b',
            r'\b(due\s*upon\s*receipt)\b',
            r'\b(cash\s*on\s*delivery|cod)\b'
        ]
        for pattern in terms_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        return None

    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Parse tabular or itemized line items."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        line_items = []

        # Regex for line pattern: description, quantity, unit price, total
        # e.g.: "Consulting Services   2   150.00   300.00"
        item_regex = re.compile(
            r'^(?P<desc>[A-Za-z0-9\s\-_/&,\.]{3,40}?)\s+'
            r'(?P<qty>\d+(?:\.\d+)?)\s+'
            r'[\$€£¥]?(?P<unit>[0-9,]+\.[0-9]{2})\s+'
            r'[\$€£¥]?(?P<total>[0-9,]+\.[0-9]{2})$'
        )

        for line in lines:
            # Skip obvious header/footer lines
            line_lower = line.lower()
            if any(h in line_lower for h in ['description', 'subtotal', 'total', 'tax', 'discount', 'invoice']):
                continue
            m = item_regex.match(line)
            if m:
                try:
                    qty = float(m.group('qty'))
                    unit = float(m.group('unit').replace(',', ''))
                    tot = float(m.group('total').replace(',', ''))
                    line_items.append({
                        "description": m.group('desc').strip(),
                        "quantity": qty,
                        "unit_price": unit,
                        "line_total": tot,
                        "tax_rate": 0.0
                    })
                except Exception:
                    continue

        return line_items


processor_service = InvoiceProcessor()
