
import os
from flask import Flask, request, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore

from config import Config  # type: ignore
from db import db_manager  # type: ignore
from invoice_processor import processor_service  # type: ignore
from ai_model import categorizer  # type: ignore

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
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]

    # Validate file
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
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
        doc_id = str(doc_id) if doc_id else None

        # Clean up file
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            "message": "Success",
            "id": doc_id,
            "invoice": fields
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Get all invoices route
@app.route("/invoices", methods=["GET"])
def get_invoices():
    try:
        invoices = db_manager.get_all_invoices()  # handles ObjectId conversion inside db_manager
        return jsonify(invoices), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dashboard summary route
@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    try:
        summary = db_manager.get_dashboard_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("message", "").lower()
    if not query:
        return jsonify({"error": "Missing message"}), 400

    stats = db_manager.get_dashboard_summary()
    if "total" in query or "spend" in query:
        response = f"📊 Total spend: **${stats['grand_total']:.2f}** ({stats['total_invoices']} invoices)."
    else:
        response = "🤖 I can help with spend totals and category breakdowns!"

    return jsonify({"response": response}), 200

# Start Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)