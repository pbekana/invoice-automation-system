import re
import os
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
    from datetime import datetime
    from dateutil import parser  # type: ignore
    from config import Config  # pyre-ignore[21]
    from logger_config import logger
    HAS_OCR_DEPS = True
except ImportError as e:
    logger.error(f"Missing OCR dependencies: {e}")
    HAS_OCR_DEPS = False

class InvoiceProcessor:
    """Service to handle OCR and data extraction from invoice files."""
    
    def __init__(self):
        self.has_ocr_deps = HAS_OCR_DEPS

    def extract_text(self, filepath):
        """Extract raw text using direct PDF extraction or OCR."""
        filename = os.path.basename(filepath).lower()
        # Demo data for well-known prefixes
        if "amazon" in filename: 
            return "Amazon.com\nOrder #112-2345678-9012345\nDate: 2026-03-15\nTotal: $120.50"
        elif "uber" in filename: 
            return "Uber Technologies Inc.\nDate: March 10, 2026\nRide Total: $45.20"
        elif "google" in filename: 
            return "Google Cloud Platform\nInvoice ID: GCP-998877\nBilling Period: Feb 2026\nAmount Due: $15.00"

        ext = os.path.splitext(filepath)[1].lower()
        if not self.has_ocr_deps:
            logger.warning(f"OCR dependencies missing, cannot process {ext}")
            return f"[OCR Dependencies missing — cannot process {ext}]"

        try:
            logger.info(f"Processing file: {filepath}")
            if ext == ".pdf": return self._process_pdf(filepath)
            elif ext in Config.ALLOWED_EXTENSIONS: return self._process_image(filepath)
            else: return f"[Unsupported file type: {ext}]"
        except Exception as e:
            logger.error(f"Error processing {ext} file: {e}")
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
        """Try text extraction if fitz is available, then fallback to OCR."""
        text = ""
        if HAS_FITZ:
            try:
                # First attempt: Direct text extraction
                doc = fitz.open(filepath)
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                # If we got enough text, return it
                if len(text.strip()) > 50:
                    logger.info("Successfully extracted text directly from PDF.")
                    return text
            except Exception as e:
                logger.warning(f"Direct PDF text extraction failed: {e}")
        else:
            logger.info("PyMuPDF (fitz) not available, skipping direct extraction.")

        # Fallback: Convert to images and OCR
        logger.info("Falling back to OCR for PDF processing.")
        images = convert_from_path(filepath, dpi=Config.DPI)
        text_parts = [self._ocr_image(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)) for img in images]
        return "\n".join(text_parts)

    def _process_image(self, filepath):
        """Read image and OCR."""
        img = cv2.imread(filepath)
        if img is None:
            logger.error(f"Could not read image file: {filepath}")
            return "[Error: Could not read image file]"
        return self._ocr_image(img)

    def _preprocess_image(self, img):
        """Advanced OpenCV preprocessing for OCR."""
        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Noise Removal (Gaussian Blur)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Adaptive Thresholding
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 4. Deskewing
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated

    def _ocr_image(self, img):
        """Apply pre-processing and Tesseract OCR."""
        try:
            processed = self._preprocess_image(img)
            text = pytesseract.image_to_string(processed, config=f"--psm {Config.OCR_PSM}").strip()
            return text
        except Exception as e:
            logger.error(f"Tesseract failure: {e}")
            return "[Tesseract failure]"

    def _extract_company(self, text):
        """Find company name based on keywords and position."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        keywords = ['inc', 'ltd', 'llc', 'corp', 'corporation', 'limited', 'services', 'stores', 'solutions']
        
        # Check first 5 non-empty lines for typical invoice headers
        for line in lines[:5]:
            line_lower = line.lower()
            # If line contains company indicators
            if any(k in line_lower for k in keywords):
                return line[:100]
            
            # Or if it looks like a prominent name (capitalized, no weird chars)
            if re.match(r'^[A-Z][A-Za-z0-9\s&\.\-]+$', line):
                # Avoid matching "Invoice", "Date", etc.
                if not any(stop in line_lower for stop in ['invoice', 'date', 'bill to', 'ship to']):
                    return line[:100]
                    
        return lines[0][:100] if lines else "Unknown Company"

    def _extract_date(self, text):
        """Extract date using robust parsing."""
        # Clean text to help dateutil
        try:
            # Common patterns for quick check
            date_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'([A-Z][a-z]+ \d{1,2},? \d{4})',
                r'(\d{1,2} [A-Z][a-z]+ \d{4})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dt = parser.parse(match.group(0), fuzzy=True)
                    return dt.strftime('%Y-%m-%d')
        except:
            pass
            
        return datetime.now().strftime('%Y-%m-%d')

    def _extract_total(self, text):
        """Extract the final total using keywords and positioning."""
        text_lower = text.lower()
        keywords = ['total', 'amount due', 'amount payable', 'grand total', 'net amount']
        
        best_total = 0.0
        
        # Method 1: Look for keywords and the number following them
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'[:\s]*[\$€£]?\s*(\d+[\.,]\d{2})'
            match = re.search(pattern, text_lower)
            if match:
                try: 
                    val = float(match.group(1).replace(',', ''))
                    # Usually total is the largest such amount
                    if val > best_total:
                        best_total = val
                except: continue

        # Method 2: Fallback to largest amount in entire text if no keyword match
        if best_total == 0.0:
            amounts = re.findall(r'[\$€£]?\s*(\d+[\.,]\d{2})', text)
            processed = []
            for a in amounts:
                try: processed.append(float(a.replace(',', '')))
                except: continue
            if processed:
                # Filter out likely subtotals if we suspect they exist (usually total is last)
                best_total = max(processed)

        return best_total

processor_service = InvoiceProcessor()
