import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger_config import logger
from invoice_processor import processor_service
from ai_model import categorizer
from db import db_manager

def test_initialization():
    logger.info("Verifying initialization...")
    assert processor_service is not None
    assert categorizer is not None
    logger.info("Initialization success.")

def test_processor():
    logger.info("Verifying processor logic...")
    # Demo data check
    text = processor_service.extract_text("non_existent_amazon_invoice.jpg")
    assert "Amazon.com" in text
    
    fields = processor_service.extract_fields("Amazon.com\nDate: 2026-03-15\nTotal: $120.50")
    assert fields["company"] == "Amazon.com"
    assert fields["date"] == "2026-03-15"
    assert fields["total"] == 120.50
    logger.info("Processor logic success.")

def test_categorizer():
    logger.info("Verifying categorizer logic...")
    cat, conf = categorizer.predict_with_confidence("Uber ride to airport")
    assert cat == "Transport"
    logger.info(f"Categorizer success: {cat}, {conf}")

if __name__ == "__main__":
    try:
        test_initialization()
        test_processor()
        test_categorizer()
        logger.info("✅ All basic verifications passed!")
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        sys.exit(1)
