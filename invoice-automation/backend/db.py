from pymongo import MongoClient  # pyre-ignore[21]
from config import Config  # pyre-ignore[21]

class DatabaseManager:
    """Handles MongoDB operations for the Invoice Automation system."""
    
    def __init__(self, uri=None, db_name=None):
        self.uri = uri or Config.MONGO_URI
        self.db_name = db_name or Config.DB_NAME
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)  # pyre-ignore
            self.db = self.client[self.db_name]  # pyre-ignore
            self.client.server_info()  # type: ignore
            print(f"✅ Successfully connected to MongoDB at {self.uri}")
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            self.db = None

    def insert_invoice(self, invoice_data):
        """Insert a single invoice document."""
        if self.db is None: return None
        try:
            result = self.db[Config.INVOICES_COLLECTION].insert_one(invoice_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error inserting invoice: {e}")
            return None

    def get_all_invoices(self):
        """Return all invoices, newest first."""
        if self.db is None: return []
        try:
            return list(self.db[Config.INVOICES_COLLECTION].find({}, {"_id": 0}).sort("_id", -1))
        except Exception as e:
            print(f"❌ Error fetching invoices: {e}")
            return []

    def get_dashboard_summary(self):
        """Aggregate dashboard stats."""
        if self.db is None: return self._empty_summary()
        try:
            collection = self.db[Config.INVOICES_COLLECTION]
            cat_pipeline = [{"$group": {"_id": "$category", "total": {"$sum": {"$ifNull": ["$total", 0]}}, "count": {"$sum": 1}}}]
            categories = {item["_id"]: {"total": float(f"{float(item['total']):.2f}"), "count": item["count"]} for item in collection.aggregate(cat_pipeline) if item["_id"]}
            total_invoices = collection.count_documents({})
            grand_total = sum(cat["total"] for cat in categories.values())
            return {"categories": categories, "total_invoices": total_invoices, "grand_total": float(f"{grand_total:.2f}")}
        except Exception as e:
            print(f"❌ Error in dashboard summary: {e}")
            return self._empty_summary()

    def _empty_summary(self):
        return {"categories": {}, "total_invoices": 0, "grand_total": 0.0}

db_manager = DatabaseManager()
