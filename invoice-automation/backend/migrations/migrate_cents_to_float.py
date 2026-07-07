import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def migrate():
    load_dotenv()
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("DB_NAME", "invoice_db")
    
    print(f"Connecting to MongoDB at {uri}, db: {db_name}")
    client = MongoClient(uri)
    db = client[db_name]
    
    collection = db[Config.INVOICES_COLLECTION]
    
    # Find all invoices
    invoices = list(collection.find({}))
    print(f"Found {len(invoices)} invoices")
    
    migrated_count = 0
    
    for inv in invoices:
        total = inv.get("total")
        
        # If total is an integer and larger than what a reasonable float would be without decimals,
        # it was likely stored in cents. For example, $50.00 was stored as 5000.
        # It's tricky to know for sure if 100 means $100 or $1.00, but the old db.py code stored *100.
        # Let's check if total is an int and has no fractional part.
        # Actually, if it's stored as int from `db.py`, it's type int.
        if isinstance(total, int):
            # It was likely stored in cents
            new_total = float(total) / 100.0
            print(f"Migrating invoice {inv['_id']}: {total} -> {new_total}")
            collection.update_one(
                {"_id": inv["_id"]},
                {"$set": {"total": float(f"{new_total:.2f}")}}
            )
            migrated_count += 1
            
    print(f"Migration complete. Updated {migrated_count} invoices.")

if __name__ == "__main__":
    migrate()
