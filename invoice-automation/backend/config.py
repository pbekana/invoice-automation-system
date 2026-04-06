import os
from dotenv import load_dotenv  # pyre-ignore[21]

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for the Invoice Automation Backend."""
    
    # Flask settings
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    
    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "invoice_db")
    INVOICES_COLLECTION = "invoices"
    
    # File handling
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"}
    
    # AI/OCR settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DPI = 300
    OCR_PSM = 6

# Ensure upload directory exists
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)
