import os
import uuid
from flask import Flask, request, jsonify, g  # type: ignore
from flask_cors import CORS  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore
from bson import ObjectId  # type: ignore

from config import Config  
from db import db_manager  # type: ignore
from invoice_processor import processor_service  # type: ignore
from ai_model import categorizer  # type: ignore
from logger_config import logger
from services.auth_service import AuthService, auth_service as _auth_service  # type: ignore
from middleware.auth import require_auth, require_roles, get_current_user_id  # type: ignore
from models.user import UserRole  # type: ignore

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Initialize auth service with database connection
auth_service = AuthService(db_manager.db)
# Update the module-level singleton
import services.auth_service as auth_module
auth_module.auth_service = auth_service

# Initialize other services
from services.vendor_service import VendorService  # type: ignore
from services.invoice_service import InvoiceService  # type: ignore
from services.audit_service import AuditService, AuditAction  # type: ignore

# Initialize Phase 4 services
from services.notification_service import NotificationService  # type: ignore
from services.approval_rules_service import ApprovalRulesService  # type: ignore

# Initialize utilities
from utils.invoice_numbers import InvoiceNumberGenerator, SequenceManager  # type: ignore
from utils.export import CSVExporter, ReportGenerator  # type: ignore
from utils.pagination import get_pagination_params  # type: ignore
from utils.filters import parse_invoice_filters, parse_vendor_filters, parse_sort_params  # type: ignore

vendor_service = VendorService(db_manager.db)
invoice_service = InvoiceService(db_manager.db)
audit_service = AuditService(db_manager.db)
sequence_manager = SequenceManager(db_manager.db)
notification_service = NotificationService(db_manager.db)
approval_rules_service = ApprovalRulesService(db_manager.db)

# Update module-level singletons
import services.vendor_service as vendor_module
import services.invoice_service as invoice_module
import services.audit_service as audit_module
import services.notification_service as notification_module
import services.approval_rules_service as approval_rules_module

vendor_module.vendor_service = vendor_service
invoice_module.invoice_service = invoice_service
audit_module.audit_service = audit_service
notification_module.notification_service = notification_service
approval_rules_module.approval_rules_service = approval_rules_service

# Initialize Phase 5 services (Customer, Product, Company)
from services.customer_service import CustomerService  # type: ignore
from services.product_service import ProductService  # type: ignore
from services.company_service import CompanyService  # type: ignore

customer_service = CustomerService(db_manager.db)
product_service = ProductService(db_manager.db)
company_service = CompanyService(db_manager.db)

import services.customer_service as customer_module
import services.product_service as product_module
import services.company_service as company_module

customer_module.customer_service = customer_service
product_module.product_service = product_service
company_module.company_service = company_service

# Initialize AI Agent Service
from services.ai_agent_service import initialize_ai_agent, get_ai_agent
ai_agent = initialize_ai_agent(db_manager)

# Initialize rate limiting (Phase 4)
from middleware.rate_limit import init_rate_limiter
limiter = init_rate_limiter(app) if Config.RATELIMIT_ENABLED else None

# Initialize request logging middleware (Phase 4)
from middleware.request_logging import log_request, log_response
app.before_request(log_request)
app.after_request(log_response)

# Helper function for SMTP config
def get_smtp_config():
    """Get SMTP configuration if notifications are enabled."""
    if not Config.NOTIFICATIONS_ENABLED:
        return None
    return {
        'host': Config.SMTP_HOST,
        'port': Config.SMTP_PORT,
        'username': Config.SMTP_USERNAME,
        'password': Config.SMTP_PASSWORD,
        'from_email': Config.SMTP_FROM_EMAIL,
        'use_tls': Config.SMTP_USE_TLS
    }

# Helper function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user (admin only in production, open for first user)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        required_fields = ["email", "name", "password"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
        
        # Register user
        success, user, error = auth_service.register_user(
            email=data["email"],
            name=data["name"],
            password=data["password"],
            roles=data.get("roles", [UserRole.SUBMITTER]),
            department=data.get("department")
        )
        
        if not success:
            return jsonify({"error": error}), 400
        
        logger.info(f"New user registered: {user.email}")
        return jsonify({
            "message": "User registered successfully",
            "user": user.to_json()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({"error": "Registration failed"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Authenticate user and return JWT tokens."""
    try:
        data = request.get_json()
        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password required"}), 400
        
        # Authenticate
        success, user, error = auth_service.authenticate(
            email=data["email"],
            password=data["password"]
        )
        
        if not success:
            return jsonify({"error": error}), 401
        
        # Generate tokens
        access_token = auth_service.generate_access_token(user)
        refresh_token = auth_service.generate_refresh_token(user)
        
        logger.info(f"User logged in: {user.email}")
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_json()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({"error": "Login failed"}), 500

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token."""
    try:
        data = request.get_json()
        if not data or not data.get("refresh_token"):
            return jsonify({"error": "Refresh token required"}), 400
        
        success, access_token, error = auth_service.refresh_access_token(data["refresh_token"])
        
        if not success:
            return jsonify({"error": error}), 401
        
        return jsonify({
            "access_token": access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        return jsonify({"error": "Token refresh failed"}), 500

@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_current_user():
    """Get current authenticated user info."""
    from flask import g
    user = g.current_user
    return jsonify({"user": user.to_json()}), 200

@app.route("/api/auth/change-password", methods=["POST"])
@require_auth
def change_password():
    """Change current user's password."""
    try:
        from flask import g
        data = request.get_json()
        
        if not data or not data.get("old_password") or not data.get("new_password"):
            return jsonify({"error": "Old and new passwords required"}), 400
        
        success, error = auth_service.change_password(
            user_id=str(g.current_user._id),
            old_password=data["old_password"],
            new_password=data["new_password"]
        )
        
        if not success:
            return jsonify({"error": error}), 400
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        return jsonify({"error": "Password change failed"}), 500

# ============================================================================
# VENDOR ROUTES (Protected)
# ============================================================================

@app.route("/api/vendors", methods=["POST"])
@require_auth
def create_vendor():
    """Create a new vendor."""
    try:
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"error": "Vendor name is required"}), 400
        
        user_id = get_current_user_id()
        
        success, vendor, error = vendor_service.create_vendor(
            name=data["name"],
            user_id=user_id,
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            tax_id=data.get("tax_id"),
            payment_terms=data.get("payment_terms"),
            default_category=data.get("default_category"),
            notes=data.get("notes")
        )
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_vendor_action(
            AuditAction.VENDOR_CREATED,
            str(vendor._id),
            user_id,
            {"name": vendor.name}
        )
        
        return jsonify({
            "message": "Vendor created successfully",
            "vendor": vendor.to_json()
        }), 201
        
    except Exception as e:
        logger.error(f"Vendor creation error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create vendor"}), 500

@app.route("/api/vendors", methods=["GET"])
@require_auth
def list_vendors():
    """List all vendors with optional filtering."""
    try:
        status = request.args.get("status")
        search = request.args.get("search")
        limit = int(request.args.get("limit", 100))
        skip = int(request.args.get("skip", 0))
        
        vendors = vendor_service.list_vendors(
            status=status,
            search=search,
            limit=min(limit, 200),  # Cap at 200
            skip=skip
        )
        
        total = vendor_service.count_vendors(status=status)
        
        return jsonify({
            "vendors": [v.to_json() for v in vendors],
            "total": total,
            "limit": limit,
            "skip": skip
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list vendors: {e}")
        return jsonify({"error": "Failed to retrieve vendors"}), 500

@app.route("/api/vendors/<vendor_id>", methods=["GET"])
@require_auth
def get_vendor(vendor_id):
    """Get vendor by ID."""
    try:
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        
        return jsonify({"vendor": vendor.to_json()}), 200
        
    except Exception as e:
        logger.error(f"Failed to get vendor: {e}")
        return jsonify({"error": "Failed to retrieve vendor"}), 500

@app.route("/api/vendors/<vendor_id>", methods=["PATCH"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def update_vendor(vendor_id):
    """Update vendor information."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        user_id = get_current_user_id()
        
        success, error = vendor_service.update_vendor(vendor_id, data)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_vendor_action(
            AuditAction.VENDOR_UPDATED,
            vendor_id,
            user_id,
            {"updates": list(data.keys())}
        )
        
        # Get updated vendor
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        
        return jsonify({
            "message": "Vendor updated successfully",
            "vendor": vendor.to_json() if vendor else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update vendor: {e}", exc_info=True)
        return jsonify({"error": "Failed to update vendor"}), 500

@app.route("/api/vendors/<vendor_id>/deactivate", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN])
def deactivate_vendor(vendor_id):
    """Deactivate a vendor."""
    try:
        user_id = get_current_user_id()
        
        success, error = vendor_service.deactivate_vendor(vendor_id)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_vendor_action(
            AuditAction.VENDOR_DEACTIVATED,
            vendor_id,
            user_id
        )
        
        return jsonify({"message": "Vendor deactivated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Failed to deactivate vendor: {e}")
        return jsonify({"error": "Failed to deactivate vendor"}), 500

@app.route("/api/vendors/<vendor_id>/block", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN])
def block_vendor(vendor_id):
    """Block a vendor."""
    try:
        data = request.get_json() or {}
        reason = data.get("reason")
        user_id = get_current_user_id()
        
        success, error = vendor_service.block_vendor(vendor_id, reason)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_vendor_action(
            AuditAction.VENDOR_BLOCKED,
            vendor_id,
            user_id,
            {"reason": reason}
        )
        
        return jsonify({"message": "Vendor blocked successfully"}), 200
        
    except Exception as e:
        logger.error(f"Failed to block vendor: {e}")
        return jsonify({"error": "Failed to block vendor"}), 500

# ============================================================================
# INVOICE ROUTES (Protected)
# ============================================================================

@app.route("/upload", methods=["POST"])
@require_auth
def upload_invoice():
    """Upload and process invoice file."""
    if "file" not in request.files:
        logger.warning("Upload attempt without file.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    # Validate file presence and extension
    if not file.filename or not allowed_file(file.filename):
        logger.warning(f"Invalid file upload attempt: {file.filename}")
        return jsonify({"error": "Invalid file type. Supported: " + ", ".join(Config.ALLOWED_EXTENSIONS)}), 400

    filepath = None
    try:
        # Get current user
        user_id = get_current_user_id()
        
        # Generate unique filename using UUID to prevent collisions
        ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        logger.info(f"Saving upload to {filepath} for user {user_id}")
        file.save(filepath)

        # Extract text and fields
        raw_text = processor_service.extract_text(filepath)
        fields = processor_service.extract_fields(raw_text)
        
        # Categorize
        category, confidence = categorizer.predict_with_confidence(raw_text)
        
        # Get or create vendor from company name
        vendor = None
        if fields.get("company"):
            success, vendor, was_created = vendor_service.get_or_create_vendor(
                name=fields["company"],
                user_id=user_id,
                default_category=str(category)
            )
            if success and was_created:
                logger.info(f"Auto-created vendor: {vendor.name}")
        
        # Check for duplicate invoices
        duplicate = None
        if fields.get("total") and fields.get("date"):
            duplicate = invoice_service.check_duplicate(
                invoice_number=None,  # We don't extract invoice numbers yet
                vendor_id=str(vendor._id) if vendor else None,
                total=fields["total"],
                date=fields["date"]
            )
        
        # Create invoice using service
        success, invoice, error = invoice_service.create_invoice(
            company=fields.get("company", "Unknown"),
            date=fields.get("date"),
            total=fields.get("total", 0.0),
            category=str(category) if category else "Supplies",
            submitter_id=user_id,
            vendor_id=str(vendor._id) if vendor else None,
            raw_text=raw_text,
            confidence=confidence,
            notes=f"Uploaded file: {file.filename}"
        )
        
        if not success:
            return jsonify({"error": error or "Failed to create invoice"}), 500
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_CREATED,
            str(invoice._id),
            user_id,
            {
                "company": invoice.company,
                "total": invoice.total,
                "category": invoice.category,
                "filename": file.filename
            }
        )
        
        # Clean up file immediately after processing
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info("Temporary file removed.")

        response_data = {
            "message": "Invoice processed successfully",
            "id": str(invoice._id),
            "invoice": invoice.to_json(),
            "vendor_created": vendor and success
        }
        
        # Warn about potential duplicate
        if duplicate:
            response_data["warning"] = f"Potential duplicate detected: Invoice {duplicate._id} from {duplicate.date}"
            response_data["duplicate_invoice_id"] = str(duplicate._id)
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred while processing the invoice. Please try again later."}), 500
    finally:
        # Emergency cleanup fallback
        if filepath and os.path.exists(filepath):
            try: os.remove(filepath)
            except: pass

# Invoice listing route (with service integration)
@app.route("/invoices", methods=["GET"])
@require_auth
def get_invoices():
    """List invoices with filtering and pagination."""
    try:
        from flask import g
        user_id = get_current_user_id()
        user_roles = g.current_user.roles if hasattr(g, 'current_user') else []
        
        # Get query parameters
        status = request.args.get("status")
        submitter_id = request.args.get("submitter_id")
        vendor_id = request.args.get("vendor_id")
        category = request.args.get("category")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = int(request.args.get("limit", 50))
        skip = int(request.args.get("skip", 0))
        
        # Use invoice service
        invoices = invoice_service.list_invoices(
            user_id=user_id,
            status=status,
            submitter_id=submitter_id,
            vendor_id=vendor_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=min(limit, 200),  # Cap at 200
            skip=skip,
            user_roles=user_roles
        )
        
        total = invoice_service.count_invoices()
        
        return jsonify({
            "invoices": [inv.to_json() for inv in invoices],
            "total": total,
            "limit": limit,
            "skip": skip
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch invoices: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve invoices"}), 500

@app.route("/api/invoices/<invoice_id>", methods=["GET"])
@require_auth
def get_invoice(invoice_id):
    """Get single invoice by ID."""
    try:
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        return jsonify({"invoice": invoice.to_json()}), 200
        
    except Exception as e:
        logger.error(f"Failed to get invoice: {e}")
        return jsonify({"error": "Failed to retrieve invoice"}), 500

@app.route("/api/invoices/<invoice_id>", methods=["PATCH"])
@require_auth
def update_invoice(invoice_id):
    """Update invoice fields (only if editable)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        user_id = get_current_user_id()
        
        success, error = invoice_service.update_invoice(invoice_id, data, user_id)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_UPDATED,
            invoice_id,
            user_id,
            {"updates": list(data.keys())}
        )
        
        # Get updated invoice
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        
        return jsonify({
            "message": "Invoice updated successfully",
            "invoice": invoice.to_json() if invoice else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update invoice: {e}", exc_info=True)
        return jsonify({"error": "Failed to update invoice"}), 500

@app.route("/api/invoices/<invoice_id>/submit", methods=["POST"])
@require_auth
def submit_invoice_for_approval(invoice_id):
    """Submit invoice for approval with automatic approver assignment."""
    try:
        user_id = get_current_user_id()
        
        # Get invoice before submission
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        # Submit for approval
        success, error = invoice_service.submit_for_approval(invoice_id, user_id)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Get updated invoice
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        invoice_dict = invoice.to_dict()
        
        # Phase 4: Determine approvers using approval rules
        approvers, required_count = approval_rules_service.determine_approvers(
            invoice_dict,
            db_manager.db.users
        )
        
        logger.info(f"Invoice {invoice_id} requires {required_count} approvals from {len(approvers)} potential approvers")
        
        # Phase 4: Send notifications to approvers
        if Config.NOTIFICATIONS_ENABLED and approvers:
            submitter = db_manager.db.users.find_one({'_id': ObjectId(user_id)})
            notification_service.notify_invoice_submitted(
                invoice_dict,
                submitter,
                approvers,
                smtp_config=get_smtp_config()
            )
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_SUBMITTED,
            invoice_id,
            user_id,
            {
                "approvers_notified": len(approvers) if approvers else 0,
                "required_approvals": required_count
            }
        )
        
        return jsonify({
            "message": "Invoice submitted for approval",
            "invoice": invoice.to_json() if invoice else None,
            "approvers_notified": len(approvers) if approvers else 0,
            "required_approvals": required_count
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to submit invoice: {e}", exc_info=True)
        return jsonify({"error": "Failed to submit invoice"}), 500

@app.route("/api/invoices/<invoice_id>/approve", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def approve_invoice(invoice_id):
    """Approve an invoice with notification to submitter."""
    try:
        data = request.get_json() or {}
        comments = data.get("comments")
        user_id = get_current_user_id()
        
        # Get invoice and approver before approval
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        approver = db_manager.db.users.find_one({'_id': ObjectId(user_id)})
        submitter = db_manager.db.users.find_one({'_id': ObjectId(invoice.submitter_id)}) if invoice.submitter_id else None
        
        # Approve invoice
        success, error = invoice_service.approve_invoice(invoice_id, user_id, comments)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Phase 4: Send notification to submitter
        if Config.NOTIFICATIONS_ENABLED and submitter:
            invoice_dict = invoice.to_dict()
            notification_service.notify_invoice_approved(
                invoice_dict,
                approver,
                submitter,
                smtp_config=get_smtp_config()
            )
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_APPROVED,
            invoice_id,
            user_id,
            {"comments": comments}
        )
        
        # Get updated invoice
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        
        return jsonify({
            "message": "Invoice approved successfully",
            "invoice": invoice.to_json() if invoice else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to approve invoice: {e}", exc_info=True)
        return jsonify({"error": "Failed to approve invoice"}), 500

@app.route("/api/invoices/<invoice_id>/reject", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def reject_invoice(invoice_id):
    """Reject an invoice with notification to submitter."""
    try:
        data = request.get_json()
        if not data or not data.get("reason"):
            return jsonify({"error": "Rejection reason is required"}), 400
        
        reason = data["reason"]
        user_id = get_current_user_id()
        
        # Get invoice and users before rejection
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        approver = db_manager.db.users.find_one({'_id': ObjectId(user_id)})
        submitter = db_manager.db.users.find_one({'_id': ObjectId(invoice.submitter_id)}) if invoice.submitter_id else None
        
        # Reject invoice
        success, error = invoice_service.reject_invoice(invoice_id, user_id, reason)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Phase 4: Send notification to submitter
        if Config.NOTIFICATIONS_ENABLED and submitter:
            invoice_dict = invoice.to_dict()
            notification_service.notify_invoice_rejected(
                invoice_dict,
                approver,
                submitter,
                comments=reason,
                smtp_config=get_smtp_config()
            )
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_REJECTED,
            invoice_id,
            user_id,
            {"reason": reason}
        )
        
        # Get updated invoice
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        
        return jsonify({
            "message": "Invoice rejected",
            "invoice": invoice.to_json() if invoice else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reject invoice: {e}", exc_info=True)
        return jsonify({"error": "Failed to reject invoice"}), 500

@app.route("/api/invoices/<invoice_id>/paid", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def mark_invoice_paid(invoice_id):
    """Mark invoice as paid."""
    try:
        data = request.get_json() or {}
        payment_reference = data.get("payment_reference")
        user_id = get_current_user_id()
        
        success, error = invoice_service.mark_as_paid(invoice_id, user_id, payment_reference)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_PAID,
            invoice_id,
            user_id,
            {"payment_reference": payment_reference}
        )
        
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        
        return jsonify({
            "message": "Invoice marked as paid",
            "invoice": invoice.to_json() if invoice else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to mark invoice as paid: {e}")
        return jsonify({"error": "Failed to mark invoice as paid"}), 500

@app.route("/api/invoices/<invoice_id>/cancel", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN])
def cancel_invoice(invoice_id):
    """Cancel an invoice."""
    try:
        data = request.get_json()
        if not data or not data.get("reason"):
            return jsonify({"error": "Cancellation reason is required"}), 400
        
        reason = data["reason"]
        user_id = get_current_user_id()
        
        success, error = invoice_service.cancel_invoice(invoice_id, user_id, reason)
        
        if not success:
            return jsonify({"error": error}), 400
        
        # Log audit
        audit_service.log_invoice_action(
            AuditAction.INVOICE_CANCELLED,
            invoice_id,
            user_id,
            {"reason": reason}
        )
        
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        
        return jsonify({
            "message": "Invoice cancelled",
            "invoice": invoice.to_json() if invoice else None
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to cancel invoice: {e}")
        return jsonify({"error": "Failed to cancel invoice"}), 500

@app.route("/api/invoices/pending-approvals", methods=["GET"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def get_pending_approvals():
    """Get invoices pending approval for current user."""
    try:
        user_id = get_current_user_id()
        
        invoices = invoice_service.get_pending_approvals(user_id)
        
        return jsonify({
            "invoices": [inv.to_json() for inv in invoices],
            "total": len(invoices)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        return jsonify({"error": "Failed to retrieve pending approvals"}), 500

@app.route("/api/invoices/<invoice_id>/history", methods=["GET"])
@require_auth
def get_invoice_history(invoice_id):
    """Get audit history for an invoice."""
    try:
        history = audit_service.get_entity_history("invoice", invoice_id)
        
        return jsonify({
            "invoice_id": invoice_id,
            "history": history
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get invoice history: {e}")
        return jsonify({"error": "Failed to retrieve invoice history"}), 500

# ============================================================================
# AUDIT ROUTES (Protected)
# ============================================================================

@app.route("/api/audit/recent", methods=["GET"])
@require_auth
@require_roles([UserRole.ADMIN])
def get_recent_audit_activity():
    """Get recent audit activity (admin only)."""
    try:
        entity_type = request.args.get("entity_type")
        action = request.args.get("action")
        limit = int(request.args.get("limit", 50))
        
        activity = audit_service.get_recent_activity(
            entity_type=entity_type,
            action=action,
            limit=min(limit, 200)
        )
        
        return jsonify({
            "activity": activity,
            "total": len(activity)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get audit activity: {e}")
        return jsonify({"error": "Failed to retrieve audit activity"}), 500

@app.route("/api/audit/user/<user_id>", methods=["GET"])
@require_auth
def get_user_audit_activity(user_id):
    """Get audit activity for a specific user."""
    try:
        from flask import g
        current_user = g.current_user
        
        # Users can only see their own activity unless they're admin
        if str(current_user._id) != user_id and not current_user.is_admin():
            return jsonify({"error": "Unauthorized"}), 403
        
        limit = int(request.args.get("limit", 100))
        
        activity = audit_service.get_user_activity(
            user_id=user_id,
            limit=min(limit, 200)
        )
        
        return jsonify({
            "user_id": user_id,
            "activity": activity,
            "total": len(activity)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get user activity: {e}")
        return jsonify({"error": "Failed to retrieve user activity"}), 500

@app.route("/api/audit/search", methods=["GET"])
@require_auth
@require_roles([UserRole.ADMIN])
def search_audit_log():
    """Search audit log with filters (admin only)."""
    try:
        user_id = request.args.get("user_id")
        entity_type = request.args.get("entity_type")
        action = request.args.get("action")
        limit = int(request.args.get("limit", 100))
        skip = int(request.args.get("skip", 0))
        
        results = audit_service.search_audit_log(
            user_id=user_id,
            entity_type=entity_type,
            action=action,
            limit=min(limit, 200),
            skip=skip
        )
        
        return jsonify({
            "results": results,
            "total": len(results),
            "limit": limit,
            "skip": skip
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to search audit log: {e}")
        return jsonify({"error": "Failed to search audit log"}), 500

# ============================================================================
# LEGACY ROUTES (Kept for backward compatibility)
# ============================================================================

# ============================================================================
# LEGACY ROUTES (Kept for backward compatibility)
# ============================================================================

# Dashboard summary route
@app.route("/dashboard", methods=["GET"])
@require_auth
def get_dashboard():
    """Get dashboard summary statistics."""
    try:
        summary = db_manager.get_dashboard_summary()
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Dashboard summary fetch failed: {e}")
        return jsonify({"error": "Failed to retrieve dashboard data"}), 500

# Chat route - AI Agent
@app.route("/chat", methods=["POST"])
@require_auth
def chat():
    """
    Intelligent AI assistant for invoice automation.
    Supports conversation memory, tool-calling, and structured outputs.
    """
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing message body"}), 400
            
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Empty message"}), 400
        
        # Get session ID for conversation memory (default to user ID)
        user_id = get_current_user_id()
        session_id = data.get("session_id", f"user_{user_id}")
        
        # Use the new AI agent service
        agent = get_ai_agent()
        if not agent:
            # Fallback to basic response if agent not configured
            return jsonify({
                "response": "AI agent is not configured. Please set up ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment variables.",
                "error": "not_configured"
            }), 503
        
        # Get response from AI agent
        result = agent.chat(
            message=message,
            session_id=session_id,
            user_id=user_id
        )
        
        # Log the interaction for audit purposes
        audit_service.log(
            action="ai_chat_query",
            entity_type="chat",
            entity_id=session_id,
            user_id=user_id,
            details={
                "message": message[:100],
                "tools_used": result.get("tools_used", []),
                "has_error": "error" in result
            }
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        return jsonify({
            "error": "Chat service encountered an error",
            "details": str(e) if Config.DEBUG else None
        }), 500


@app.route("/chat/history/clear", methods=["POST"])
@require_auth
def clear_chat_history():
    """Clear conversation history for the current session"""
    try:
        data = request.get_json() or {}
        user_id = get_current_user_id()
        session_id = data.get("session_id", f"user_{user_id}")
        
        agent = get_ai_agent()
        if agent:
            agent.clear_history(session_id)
            return jsonify({"message": "Chat history cleared"}), 200
        
        return jsonify({"error": "AI agent not available"}), 503
        
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        return jsonify({"error": "Failed to clear history"}), 500

# ============================================================================
# PHASE 3: EXPORT & REPORTING ENDPOINTS
# ============================================================================

@app.route("/api/export/invoices", methods=["GET"])
@require_auth
def export_invoices_csv():
    """Export invoices to CSV format."""
    try:
        from flask import make_response
        from datetime import datetime
        user_id = get_current_user_id()
        user_roles = g.current_user.roles if hasattr(g, 'current_user') else []
        
        # Get filters from query params
        status = request.args.get("status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        category = request.args.get("category")
        
        # Get invoices using service
        invoices = invoice_service.list_invoices(
            user_id=user_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=10000,
            skip=0,
            user_roles=user_roles
        )
        
        invoice_dicts = [inv.to_json() for inv in invoices]
        csv_data = CSVExporter.export_invoices(invoice_dicts)
        
        response = make_response(csv_data)
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = f"attachment; filename=invoices_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        audit_service.log(
            action="invoices_exported",
            entity_type="invoice",
            entity_id="bulk",
            user_id=user_id,
            details={"count": len(invoices)}
        )
        
        return response
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return jsonify({"error": "Failed to export invoices"}), 500

@app.route("/api/reports/spending-summary", methods=["GET"])
@require_auth
def get_spending_summary():
    """Get spending summary report."""
    try:
        user_id = get_current_user_id()
        user_roles = g.current_user.roles if hasattr(g, 'current_user') else []
        
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        category = request.args.get("category")
        
        invoices = invoice_service.list_invoices(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=10000,
            skip=0,
            user_roles=user_roles
        )
        
        invoice_dicts = [inv.to_json() for inv in invoices]
        summary = ReportGenerator.generate_spending_summary(invoice_dicts)
        
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({"error": "Failed to generate report"}), 500

@app.route("/api/invoices/bulk/approve", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN, UserRole.APPROVER])
def bulk_approve_invoices():
    """Bulk approve multiple invoices."""
    try:
        data = request.get_json()
        if not data or not data.get("invoice_ids"):
            return jsonify({"error": "invoice_ids required"}), 400
        
        invoice_ids = data["invoice_ids"]
        comments = data.get("comments", "Bulk approved")
        user_id = get_current_user_id()
        
        results = {"successful": [], "failed": []}
        
        for invoice_id in invoice_ids:
            success, error = invoice_service.approve_invoice(invoice_id, user_id, comments)
            if success:
                results["successful"].append(invoice_id)
                audit_service.log_invoice_action(
                    AuditAction.INVOICE_APPROVED,
                    invoice_id,
                    user_id,
                    {"bulk_operation": True}
                )
            else:
                results["failed"].append({"invoice_id": invoice_id, "error": error})
        
        return jsonify({
            "message": f"Approved {len(results['successful'])} of {len(invoice_ids)} invoices",
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Bulk approve failed: {e}")
        return jsonify({"error": "Bulk approve operation failed"}), 500

@app.route("/api/dashboard/enhanced", methods=["GET"])
@require_auth
def get_enhanced_dashboard():
    """Get enhanced dashboard with workflow metrics."""
    try:
        user_id = get_current_user_id()
        user_roles = g.current_user.roles if hasattr(g, 'current_user') else []
        
        invoices = invoice_service.list_invoices(
            user_id=user_id,
            limit=10000,
            skip=0,
            user_roles=user_roles
        )
        
        invoice_dicts = [inv.to_json() for inv in invoices]
        summary = ReportGenerator.generate_spending_summary(invoice_dicts)
        
        # Workflow metrics
        pending_count = len([inv for inv in invoice_dicts if inv.get("status") == "pending_approval"])
        approved_count = len([inv for inv in invoice_dicts if inv.get("status") == "approved"])
        paid_count = len([inv for inv in invoice_dicts if inv.get("status") == "paid"])
        
        dashboard_data = {
            **summary,
            "workflow_metrics": {
                "pending_approval": pending_count,
                "approved": approved_count,
                "paid": paid_count
            }
        }
        
        return jsonify(dashboard_data), 200
    except Exception as e:
        logger.error(f"Enhanced dashboard failed: {e}", exc_info=True)
        return jsonify({"error": "Failed to load enhanced dashboard"}), 500

# ============================================================================
# PHASE 4: APPROVAL RULES & NOTIFICATIONS ENDPOINTS
# ============================================================================

@app.route("/api/approval-rules", methods=["GET"])
@require_auth
@require_roles([UserRole.ADMIN])
def get_approval_rules():
    """Get all approval rules (admin only)."""
    try:
        active_only = request.args.get("active_only", "true").lower() == "true"
        rules = approval_rules_service.get_all_rules(active_only=active_only)
        
        return jsonify({
            "rules": [rule.to_dict() for rule in rules]
        }), 200
    except Exception as e:
        logger.error(f"Failed to get approval rules: {e}")
        return jsonify({"error": "Failed to retrieve approval rules"}), 500

@app.route("/api/approval-rules", methods=["POST"])
@require_auth
@require_roles([UserRole.ADMIN])
def create_approval_rule():
    """Create a new approval rule (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        required = ["rule_id", "name", "conditions", "approvers"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
        
        success, rule_doc, error = approval_rules_service.create_rule(
            rule_id=data["rule_id"],
            name=data["name"],
            conditions=data["conditions"],
            approvers=data["approvers"],
            required_approvals=data.get("required_approvals", 1),
            priority=data.get("priority", 0)
        )
        
        if not success:
            return jsonify({"error": error}), 400
        
        user_id = get_current_user_id()
        audit_service.log(
            action="approval_rule_created",
            entity_type="approval_rule",
            entity_id=data["rule_id"],
            user_id=user_id,
            details={"name": data["name"]}
        )
        
        return jsonify({
            "message": "Approval rule created successfully",
            "rule": rule_doc
        }), 201
    except Exception as e:
        logger.error(f"Failed to create approval rule: {e}")
        return jsonify({"error": "Failed to create approval rule"}), 500

@app.route("/api/approval-rules/<rule_id>", methods=["PATCH"])
@require_auth
@require_roles([UserRole.ADMIN])
def update_approval_rule(rule_id):
    """Update an approval rule (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        success, error = approval_rules_service.update_rule(rule_id, data)
        
        if not success:
            return jsonify({"error": error}), 400
        
        user_id = get_current_user_id()
        audit_service.log(
            action="approval_rule_updated",
            entity_type="approval_rule",
            entity_id=rule_id,
            user_id=user_id,
            details={"updates": list(data.keys())}
        )
        
        return jsonify({"message": "Approval rule updated successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to update approval rule: {e}")
        return jsonify({"error": "Failed to update approval rule"}), 500

@app.route("/api/approval-rules/<rule_id>", methods=["DELETE"])
@require_auth
@require_roles([UserRole.ADMIN])
def delete_approval_rule(rule_id):
    """Deactivate an approval rule (admin only)."""
    try:
        success, error = approval_rules_service.delete_rule(rule_id)
        
        if not success:
            return jsonify({"error": error}), 400
        
        user_id = get_current_user_id()
        audit_service.log(
            action="approval_rule_deleted",
            entity_type="approval_rule",
            entity_id=rule_id,
            user_id=user_id
        )
        
        return jsonify({"message": "Approval rule deactivated successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to delete approval rule: {e}")
        return jsonify({"error": "Failed to delete approval rule"}), 500

@app.route("/api/notifications", methods=["GET"])
@require_auth
def get_user_notifications():
    """Get notifications for the current user."""
    try:
        user_id = get_current_user_id()
        limit = int(request.args.get("limit", 50))
        
        notifications = notification_service.get_user_notifications(user_id, limit=limit)
        
        # Convert ObjectId to string for JSON serialization
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
            if 'recipient_id' in notif:
                notif['recipient_id'] = str(notif['recipient_id'])
            if 'invoice_id' in notif:
                notif['invoice_id'] = str(notif['invoice_id'])
        
        return jsonify({
            "notifications": notifications,
            "count": len(notifications)
        }), 200
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        return jsonify({"error": "Failed to retrieve notifications"}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db_manager.db.command('ping')
        
        return jsonify({
            "status": "healthy",
            "services": {
                "database": "connected",
                "rate_limiting": "enabled" if Config.RATELIMIT_ENABLED else "disabled",
                "notifications": "enabled" if Config.NOTIFICATIONS_ENABLED else "disabled"
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

# ============================================================================
# CUSTOMER ROUTES (Phase 5)
# ============================================================================

@app.route("/api/customers", methods=["POST"])
@require_auth
def create_customer():
    """Create a new customer."""
    try:
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"error": "Customer name is required"}), 400

        user_id = get_current_user_id()
        success, customer, error = customer_service.create_customer(
            name=data["name"],
            user_id=user_id,
            email=data.get("email"),
            phone=data.get("phone"),
            billing_address=data.get("billing_address"),
            shipping_address=data.get("shipping_address"),
            tax_id=data.get("tax_id"),
            payment_terms=data.get("payment_terms"),
            currency=data.get("currency", "USD"),
            notes=data.get("notes"),
        )
        if not success:
            return jsonify({"error": error}), 400
        return jsonify({"message": "Customer created", "customer": customer.to_json()}), 201
    except Exception as e:
        logger.error(f"Create customer error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create customer"}), 500


@app.route("/api/customers", methods=["GET"])
@require_auth
def list_customers():
    """List all customers."""
    try:
        search = request.args.get("search")
        status = request.args.get("status")
        limit = int(request.args.get("limit", 100))
        skip = int(request.args.get("skip", 0))
        customers = customer_service.list_customers(status=status, search=search, limit=limit, skip=skip)
        return jsonify({
            "customers": [c.to_json() for c in customers],
            "total": customer_service.count_customers()
        }), 200
    except Exception as e:
        logger.error(f"List customers error: {e}", exc_info=True)
        return jsonify({"error": "Failed to list customers"}), 500


@app.route("/api/customers/<customer_id>", methods=["GET"])
@require_auth
def get_customer(customer_id):
    """Get a single customer by ID."""
    customer = customer_service.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({"customer": customer.to_json()}), 200


@app.route("/api/customers/<customer_id>", methods=["PATCH"])
@require_auth
def update_customer(customer_id):
    """Update a customer."""
    try:
        data = request.get_json() or {}
        success, error = customer_service.update_customer(customer_id, data)
        if not success:
            return jsonify({"error": error}), 400
        updated = customer_service.get_customer_by_id(customer_id)
        return jsonify({"message": "Customer updated", "customer": updated.to_json() if updated else {}}), 200
    except Exception as e:
        logger.error(f"Update customer error: {e}", exc_info=True)
        return jsonify({"error": "Failed to update customer"}), 500


@app.route("/api/customers/<customer_id>", methods=["DELETE"])
@require_auth
@require_roles([UserRole.ADMIN])
def delete_customer(customer_id):
    """Deactivate a customer (soft delete)."""
    success, error = customer_service.delete_customer(customer_id)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Customer deactivated"}), 200


# ============================================================================
# PRODUCT ROUTES (Phase 5)
# ============================================================================

@app.route("/api/products", methods=["POST"])
@require_auth
def create_product():
    """Create a new product or service."""
    try:
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"error": "Product name is required"}), 400

        user_id = get_current_user_id()
        success, product, error = product_service.create_product(
            name=data["name"],
            user_id=user_id,
            sku=data.get("sku"),
            description=data.get("description"),
            unit_price=float(data.get("unit_price", 0.0)),
            tax_rate=float(data.get("tax_rate", 0.0)),
            category=data.get("category"),
        )
        if not success:
            return jsonify({"error": error}), 400
        return jsonify({"message": "Product created", "product": product.to_json()}), 201
    except Exception as e:
        logger.error(f"Create product error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create product"}), 500


@app.route("/api/products", methods=["GET"])
@require_auth
def list_products():
    """List all products and services."""
    try:
        search = request.args.get("search")
        active_only = request.args.get("active_only", "true").lower() == "true"
        limit = int(request.args.get("limit", 200))
        products = product_service.list_products(search=search, active_only=active_only, limit=limit)
        return jsonify({
            "products": [p.to_json() for p in products],
            "total": product_service.count_products()
        }), 200
    except Exception as e:
        logger.error(f"List products error: {e}", exc_info=True)
        return jsonify({"error": "Failed to list products"}), 500


@app.route("/api/products/<product_id>", methods=["GET"])
@require_auth
def get_product(product_id):
    product = product_service.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product.to_json()}), 200


@app.route("/api/products/<product_id>", methods=["PATCH"])
@require_auth
def update_product(product_id):
    try:
        data = request.get_json() or {}
        success, error = product_service.update_product(product_id, data)
        if not success:
            return jsonify({"error": error}), 400
        updated = product_service.get_product_by_id(product_id)
        return jsonify({"message": "Product updated", "product": updated.to_json() if updated else {}}), 200
    except Exception as e:
        logger.error(f"Update product error: {e}", exc_info=True)
        return jsonify({"error": "Failed to update product"}), 500


@app.route("/api/products/<product_id>", methods=["DELETE"])
@require_auth
@require_roles([UserRole.ADMIN])
def delete_product(product_id):
    success, error = product_service.delete_product(product_id)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Product deactivated"}), 200


# ============================================================================
# COMPANY PROFILE ROUTES (Phase 5)
# ============================================================================

@app.route("/api/company", methods=["GET"])
@require_auth
def get_company():
    """Get the company profile for the current user."""
    user_id = get_current_user_id()
    company = company_service.get_company(user_id)
    if not company:
        return jsonify({"company": None}), 200
    return jsonify({"company": company.to_json()}), 200


@app.route("/api/company", methods=["POST", "PUT"])
@require_auth
def upsert_company():
    """Create or update the company profile for the current user."""
    try:
        data = request.get_json() or {}
        user_id = get_current_user_id()
        success, company, error = company_service.upsert_company(user_id, data)
        if not success:
            return jsonify({"error": error}), 400
        return jsonify({"message": "Company profile saved", "company": company.to_json()}), 200
    except Exception as e:
        logger.error(f"Upsert company error: {e}", exc_info=True)
        return jsonify({"error": "Failed to save company profile"}), 500


# ============================================================================
# AR INVOICE ROUTES (Phase 5 — Accounts Receivable)
# ============================================================================

@app.route("/api/ar/invoices", methods=["POST"])
@require_auth
def create_ar_invoice():
    """Create a new outgoing (AR) invoice to a customer."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        required = ["customer_id", "line_items"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        user_id = get_current_user_id()

        # Validate customer exists
        customer = customer_service.get_customer_by_id(data["customer_id"])
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        # Calculate totals from line items
        line_items = data.get("line_items", [])
        subtotal = sum(
            float(item.get("quantity", 1)) * float(item.get("unit_price", 0))
            for item in line_items
        )
        tax_amount = sum(
            float(item.get("quantity", 1)) * float(item.get("unit_price", 0)) * float(item.get("tax_rate", 0)) / 100
            for item in line_items
        )
        discount = float(data.get("discount", 0))
        total = round(subtotal + tax_amount - discount, 2)

        # Generate invoice number
        seq_manager = sequence_manager
        inv_number = seq_manager.next_sequence("ar_invoice") if seq_manager else f"AR-{uuid.uuid4().hex[:8].upper()}"
        prefix = data.get("invoice_prefix", "INV-")
        invoice_number = f"{prefix}{inv_number}"

        import datetime as dt
        doc = {
            "type": "receivable",
            "invoice_number": invoice_number,
            "customer_id": data["customer_id"],
            "customer_name": customer.name,
            "customer_email": customer.email,
            "line_items": line_items,
            "subtotal": round(subtotal, 2),
            "tax_amount": round(tax_amount, 2),
            "discount": discount,
            "total": total,
            "currency": data.get("currency", customer.currency or "USD"),
            "status": data.get("status", "draft"),
            "due_date": data.get("due_date"),
            "issue_date": data.get("issue_date", dt.datetime.utcnow().strftime("%Y-%m-%d")),
            "notes": data.get("notes", ""),
            "terms": data.get("terms", ""),
            "created_by": user_id,
            "created_at": dt.datetime.utcnow(),
            "updated_at": dt.datetime.utcnow(),
        }

        db = db_manager.db
        result = db["ar_invoices"].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        doc["id"] = doc["_id"]
        doc.pop("_id")
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].isoformat()

        logger.info(f"AR invoice created: {invoice_number} by user {user_id}")
        return jsonify({"message": "Invoice created", "invoice": doc}), 201

    except Exception as e:
        logger.error(f"Create AR invoice error: {e}", exc_info=True)
        return jsonify({"error": "Failed to create invoice"}), 500


@app.route("/api/ar/invoices", methods=["GET"])
@require_auth
def list_ar_invoices():
    """List all AR invoices."""
    try:
        status = request.args.get("status")
        search = request.args.get("search")
        limit = int(request.args.get("limit", 50))
        skip = int(request.args.get("skip", 0))

        query: dict = {"type": "receivable"}
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"invoice_number": {"$regex": search, "$options": "i"}},
                {"customer_name": {"$regex": search, "$options": "i"}},
            ]

        db = db_manager.db
        docs = list(db["ar_invoices"].find(query).sort("created_at", -1).skip(skip).limit(limit))
        total = db["ar_invoices"].count_documents(query)

        serialized = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            for field in ["created_at", "updated_at"]:
                if field in d and hasattr(d[field], "isoformat"):
                    d[field] = d[field].isoformat()
            serialized.append(d)

        return jsonify({"invoices": serialized, "total": total}), 200
    except Exception as e:
        logger.error(f"List AR invoices error: {e}", exc_info=True)
        return jsonify({"error": "Failed to list invoices"}), 500


@app.route("/api/ar/invoices/<invoice_id>", methods=["GET"])
@require_auth
def get_ar_invoice(invoice_id):
    """Get a single AR invoice."""
    try:
        db = db_manager.db
        doc = db["ar_invoices"].find_one({"_id": ObjectId(invoice_id)})
        if not doc:
            return jsonify({"error": "Invoice not found"}), 404
        doc["id"] = str(doc.pop("_id"))
        for field in ["created_at", "updated_at"]:
            if field in doc and hasattr(doc[field], "isoformat"):
                doc[field] = doc[field].isoformat()
        return jsonify({"invoice": doc}), 200
    except Exception as e:
        logger.error(f"Get AR invoice error: {e}", exc_info=True)
        return jsonify({"error": "Failed to get invoice"}), 500


@app.route("/api/ar/invoices/<invoice_id>", methods=["PATCH"])
@require_auth
def update_ar_invoice(invoice_id):
    """Update an AR invoice (only draft invoices can be fully edited)."""
    try:
        import datetime as dt
        data = request.get_json() or {}
        db = db_manager.db
        existing = db["ar_invoices"].find_one({"_id": ObjectId(invoice_id)})
        if not existing:
            return jsonify({"error": "Invoice not found"}), 404

        # Recalculate totals if line_items are being updated
        if "line_items" in data:
            line_items = data["line_items"]
            subtotal = sum(
                float(item.get("quantity", 1)) * float(item.get("unit_price", 0))
                for item in line_items
            )
            tax_amount = sum(
                float(item.get("quantity", 1)) * float(item.get("unit_price", 0)) * float(item.get("tax_rate", 0)) / 100
                for item in line_items
            )
            discount = float(data.get("discount", existing.get("discount", 0)))
            data["subtotal"] = round(subtotal, 2)
            data["tax_amount"] = round(tax_amount, 2)
            data["discount"] = discount
            data["total"] = round(subtotal + tax_amount - discount, 2)

        protected = ["_id", "type", "created_at", "created_by", "invoice_number"]
        for f in protected:
            data.pop(f, None)
        data["updated_at"] = dt.datetime.utcnow()

        db["ar_invoices"].update_one({"_id": ObjectId(invoice_id)}, {"$set": data})
        updated = db["ar_invoices"].find_one({"_id": ObjectId(invoice_id)})
        updated["id"] = str(updated.pop("_id"))
        for field in ["created_at", "updated_at"]:
            if field in updated and hasattr(updated[field], "isoformat"):
                updated[field] = updated[field].isoformat()
        return jsonify({"message": "Invoice updated", "invoice": updated}), 200
    except Exception as e:
        logger.error(f"Update AR invoice error: {e}", exc_info=True)
        return jsonify({"error": "Failed to update invoice"}), 500


@app.route("/api/ar/invoices/<invoice_id>/send", methods=["POST"])
@require_auth
def send_ar_invoice(invoice_id):
    """Mark an AR invoice as 'sent'."""
    try:
        import datetime as dt
        db = db_manager.db
        result = db["ar_invoices"].update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {"status": "sent", "sent_at": dt.datetime.utcnow(), "updated_at": dt.datetime.utcnow()}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Invoice not found"}), 404
        return jsonify({"message": "Invoice marked as sent"}), 200
    except Exception as e:
        logger.error(f"Send AR invoice error: {e}", exc_info=True)
        return jsonify({"error": "Failed to send invoice"}), 500


@app.route("/api/ar/invoices/<invoice_id>/paid", methods=["POST"])
@require_auth
def mark_ar_invoice_paid(invoice_id):
    """Mark an AR invoice as paid."""
    try:
        import datetime as dt
        data = request.get_json() or {}
        db = db_manager.db
        result = db["ar_invoices"].update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {
                "status": "paid",
                "paid_at": dt.datetime.utcnow(),
                "payment_method": data.get("payment_method", ""),
                "payment_reference": data.get("payment_reference", ""),
                "updated_at": dt.datetime.utcnow()
            }}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Invoice not found"}), 404
        return jsonify({"message": "Invoice marked as paid"}), 200
    except Exception as e:
        logger.error(f"Mark AR paid error: {e}", exc_info=True)
        return jsonify({"error": "Failed to mark as paid"}), 500


# Start Flask app
if __name__ == "__main__":
    logger.info(f"Starting server on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
