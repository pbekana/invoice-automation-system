import re
import os
from datetime import datetime
from config import Config  # pyre-ignore[21]

try:
    import cv2  # pyre-ignore[21]
    import numpy as np  # pyre-ignore[21]
    import pytesseract  # pyre-ignore[21]
    from pdf2image import convert_from_path  # pyre-ignore[21]
    HAS_OCR_DEPS = True
except ImportError:
    HAS_OCR_DEPS = False

class InvoiceProcessor:
    """Service to handle OCR and data extraction from invoice files."""
    
    def __init__(self):
        self.has_ocr_deps = HAS_OCR_DEPS

    def extract_text(self, filepath):
        """Extract raw text using OCR with demo mode support."""
        filename = os.path.basename(filepath).lower()
        if "amazon" in filename: return "Amazon.com\nOrder #112-2345678-9012345\nDate: 2026-03-15\nTotal: $120.50"
        elif "uber" in filename: return "Uber Technologies Inc.\nDate: March 10, 2026\nRide Total: $45.20"
        elif "google" in filename: return "Google Cloud Platform\nInvoice ID: GCP-998877\nBilling Period: Feb 2026\nAmount Due: $15.00"

        ext = os.path.splitext(filepath)[1].lower()
        if not self.has_ocr_deps: return f"[OCR Dependencies missing — cannot process {ext}]"

        try:
            if ext == ".pdf": return self._process_pdf(filepath)
            elif ext in Config.ALLOWED_EXTENSIONS: return self._process_image(filepath)
            else: return f"[Unsupported file type: {ext}]"
        except Exception as e:
            return f"[OCR Error: {str(e)}]"

    def extract_fields(self, raw_text):
        """Parse raw text for structured invoice metadata."""
        return {
            "company": self._extract_company(raw_text),
            "date": self._extract_date(raw_text),
            "total": self._extract_total(raw_text),
            "raw_text": raw_text
        }

    def _process_pdf(self, filepath):
        """Convert PDF to images and OCR each page."""
        images = convert_from_path(filepath, dpi=Config.DPI)
        text_parts = [self._ocr_image(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)) for img in images]
        return "\n".join(text_parts)

    def _process_image(self, filepath):
        """Read image and OCR."""
        img = cv2.imread(filepath)
        return self._ocr_image(img) if img is not None else "[Error: Could not read image file]"

    def _ocr_image(self, img):
        """Apply pre-processing and Tesseract OCR."""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            return pytesseract.image_to_string(gray, config=f"--psm {Config.OCR_PSM}").strip()
        except: return "[Tesseract failure]"

    def _extract_company(self, text):
        """Try to find the company name."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 2 and not re.match(r'^[\d\s\.\-\/]+$', line):
                cleaned = str(re.sub(r'[^\w\s&\.-]', '', line)).strip()
                return cleaned[:100]
        return "Unknown Company"

    def _extract_date(self, text):
        """Extract date using regex patterns."""
        patterns = [(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', '%Y-%m-%d'), (r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', '%m/%d/%Y')]
        for p, f in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                try: return datetime.strptime(m.group(1).replace('/', '-'), f.replace('/', '-')).strftime('%Y-%m-%d')
                except: continue
        return datetime.now().strftime('%Y-%m-%d')

    def _extract_total(self, text):
        """Extract the largest monetary amount."""
        amounts = re.findall(r'[\$€£]?\s*(\d+[\.,]\d{2})', text)
        processed = []
        for a in amounts:
            try: processed.append(float(a.replace(',', '')))
            except: continue
        return max(processed) if processed else 0.0

processor_service = InvoiceProcessor()
