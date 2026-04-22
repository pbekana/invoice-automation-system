import os
import uuid
from flask import Flask, request, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore

from config import Config  # type: ignore
from db import db_manager  # type: ignore
from invoice_processor import processor_service  # type: ignore
from ai_model import categorizer  # type: ignore
from logger_config import logger

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Helper function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Upload invoice route
@app.route("/upload", methods=["POST"])
def upload_invoice():
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
        # Generate unique filename using UUID to prevent collisions
        ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        logger.info(f"Saving upload to {filepath}")
        file.save(filepath)

        # Extract text and fields
        raw_text = processor_service.extract_text(filepath)
        fields = processor_service.extract_fields(raw_text)
        
        # Categorize
        category, confidence = categorizer.predict_with_confidence(raw_text)
        
        # Ensure JSON serializable
        fields["category"] = str(category) if category else "Unknown"
        fields["confidence"] = {
            str(k): float(v) if v is not None else 0.0
            for k, v in confidence.items()
        }
        
        # Insert into DB
        doc_id = db_manager.insert_invoice(fields)
        
        # Clean up file immediately after processing
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info("Temporary file removed.")

        return jsonify({
            "message": "Invoice processed successfully",
            "id": str(doc_id) if doc_id else None,
            "invoice": fields
        }), 200

    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        # Safe error message
        return jsonify({"error": "An internal error occurred while processing the invoice. Please try again later."}), 500
    finally:
        # Emergency cleanup fallback
        if filepath and os.path.exists(filepath):
            try: os.remove(filepath)
            except: pass

# Get all invoices route
@app.route("/invoices", methods=["GET"])
def get_invoices():
    try:
        invoices = db_manager.get_all_invoices()
        return jsonify(invoices), 200
    except Exception as e:
        logger.error(f"Failed to fetch invoices: {e}")
        return jsonify({"error": "Failed to retrieve invoices"}), 500

# Dashboard summary route
@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    try:
        summary = db_manager.get_dashboard_summary()
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Dashboard summary fetch failed: {e}")
        return jsonify({"error": "Failed to retrieve dashboard data"}), 500

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing message body"}), 400
            
        query = data.get("message", "").lower()
        stats = db_manager.get_dashboard_summary()
        
        if "total" in query or "spend" in query:
            response = f"📊 Total spend: **${stats['grand_total']:.2f}** ({stats['total_invoices']} invoices)."
        else:
            response = "🤖 I can help with spend totals and category breakdowns!"

        return jsonify({"response": response}), 200
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        return jsonify({"error": "Chat service unavailable"}), 500

# Start Flask app
if __name__ == "__main__":
    logger.info(f"Starting server on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)