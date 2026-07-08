import os
from dotenv import load_dotenv  # pyre-ignore[21]

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for the Invoice Automation Backend."""
    
    # Flask settings
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "invoice_db")
    INVOICES_COLLECTION = "invoices"
    USERS_COLLECTION = "users"
    VENDORS_COLLECTION = "vendors"
    AUDIT_LOG_COLLECTION = "audit_logs"
    NOTIFICATIONS_COLLECTION = "notifications"
    APPROVAL_RULES_COLLECTION = "approval_rules"
    CUSTOMERS_COLLECTION = "customers"
    PRODUCTS_COLLECTION = "products"
    COMPANIES_COLLECTION = "companies"
    
    # Authentication settings
    _jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not _jwt_secret and not os.getenv("FLASK_DEBUG", "false").lower() == "true":
        raise RuntimeError("JWT_SECRET_KEY must be set in production!")
    import secrets
    JWT_SECRET_KEY = _jwt_secret or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days
    
    # File handling
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"}
    
    # AI/OCR settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # 'anthropic' or 'openai'
    DPI = 300
    OCR_PSM = 6
    MODEL_PATH = os.path.join(BASE_DIR, "invoice_model.joblib")
    
    # Security settings
    BCRYPT_LOG_ROUNDS = 12
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    
    # Rate limiting settings
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")  # Use "redis://localhost:6379" for Redis
    RATELIMIT_STRATEGY = "fixed-window"
    
    # Notification settings
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USERNAME", "noreply@invoiceapp.com"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true"
    
    # Approval rules settings
    APPROVAL_ESCALATION_DAYS = int(os.getenv("APPROVAL_ESCALATION_DAYS", 3))
    AUTO_APPROVAL_ENABLED = os.getenv("AUTO_APPROVAL_ENABLED", "false").lower() == "true"

# Ensure upload directory exists
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)
