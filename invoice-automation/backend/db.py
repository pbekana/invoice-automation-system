from pymongo import MongoClient, ASCENDING  # pyre-ignore[21]
from config import Config  # pyre-ignore[21]
from logger_config import logger

class DatabaseManager:
    """Handles MongoDB operations for the Invoice Automation system."""
    
    def __init__(self, uri=None, db_name=None):
        self.uri = uri or Config.MONGO_URI
        self.db_name = db_name or Config.DB_NAME
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB and ensure indexes."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)  # pyre-ignore
            self.db = self.client[self.db_name]  # pyre-ignore
            self.client.server_info()  # type: ignore
            self._ensure_indexes()
            logger.info(f"Connected to MongoDB at {self.uri}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.db = None

    def _ensure_indexes(self):
        """Create indexes for performance."""
        if self.db is not None:
            self.db[Config.INVOICES_COLLECTION].create_index([("category", ASCENDING)])
            self.db[Config.INVOICES_COLLECTION].create_index([("date", ASCENDING)])
            logger.info("Database indexes ensured.")

    @staticmethod
    def to_cents(amount_float):
        """Convert float amount to integer cents."""
        try:
            return int(round(float(amount_float) * 100))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def from_cents(amount_cents):
        """Convert integer cents back to float."""
        try:
            return float(amount_cents) / 100.0
        except (ValueError, TypeError):
            return 0.0

    def insert_invoice(self, invoice_data):
        """Insert a single invoice document."""
        if self.db is None:
            return None
        try:
            # Ensure total is in cents before saving
            if "total" in invoice_data:
                invoice_data["total"] = self.to_cents(invoice_data["total"])
            
            result = self.db[Config.INVOICES_COLLECTION].insert_one(invoice_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting invoice: {e}")
            return None

    def get_all_invoices(self):
        """Return all invoices, newest first with formatting."""
        if self.db is None:
            return []

        try:
            invoices = list(
                self.db[Config.INVOICES_COLLECTION].find().sort("_id", -1)
            )

            for inv in invoices:
                inv["_id"] = str(inv["_id"])
                if "total" in inv:
                    inv["total"] = self.from_cents(inv["total"])

            return invoices

        except Exception as e:
            logger.error(f"Error fetching invoices: {e}")
            return []

    def get_dashboard_summary(self):
        """Aggregate dashboard stats with cents-to-float conversion."""
        if self.db is None:
            return self._empty_summary()
        try:
            collection = self.db[Config.INVOICES_COLLECTION]
            cat_pipeline = [{
                "$group": {
                    "_id": "$category",
                    "total_cents": {"$sum": {"$ifNull": ["$total", 0]}},
                    "count": {"$sum": 1}
                }
            }]
            categories = {
                item["_id"]: {
                    "total": self.from_cents(item["total_cents"]),
                    "count": item["count"]
                }
                for item in collection.aggregate(cat_pipeline) if item["_id"]
            }
            total_invoices = collection.count_documents({})
            grand_total = sum(cat["total"] for cat in categories.values())
            return {
                "categories": categories,
                "total_invoices": total_invoices,
                "grand_total": float(f"{grand_total:.2f}")
            }
        except Exception as e:
            logger.error(f"Error in dashboard summary: {e}")
            return self._empty_summary()

    def _empty_summary(self):
        return {"categories": {}, "total_invoices": 0, "grand_total": 0.0}

db_manager = DatabaseManager()
