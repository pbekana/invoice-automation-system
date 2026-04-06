import os
from flask import Flask, request, jsonify  # pyre-ignore[21]
from flask_cors import CORS  # pyre-ignore[21]
from werkzeug.utils import secure_filename  # pyre-ignore[21]

from config import Config  # pyre-ignore[21]
from db import db_manager  # pyre-ignore[21]
from invoice_processor import processor_service  # pyre-ignore[21]
from ai_model import categorizer  # pyre-ignore[21]

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_invoice():
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename): return jsonify({"error": "Invalid file"}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        raw_text = processor_service.extract_text(filepath)
        fields = processor_service.extract_fields(raw_text)
        category, confidence = categorizer.predict_with_confidence(raw_text)
        fields.update({"category": category, "confidence": confidence})
        
        doc_id = db_manager.insert_invoice(fields)
        if os.path.exists(filepath): os.remove(filepath)
        
        return jsonify({"message": "Success", "id": doc_id, "data": fields}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/invoices", methods=["GET"])
def get_invoices():
    return jsonify(db_manager.get_all_invoices()), 200

@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    return jsonify(db_manager.get_dashboard_summary()), 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("message", "").lower()
    if not query: return jsonify({"error": "Missing message"}), 400
    
    stats = db_manager.get_dashboard_summary()
    if "total" in query or "spend" in query:
        response = f"📊 Total spend: **${stats['grand_total']:.2f}** ({stats['total_invoices']} invoices)."
    else:
        response = "🤖 I can help with spend totals and category breakdowns!"
    return jsonify({"response": response}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
