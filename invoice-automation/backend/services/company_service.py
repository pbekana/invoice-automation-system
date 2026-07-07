"""Company profile management service."""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from config import Config  # type: ignore
from models.company import Company  # type: ignore
from logger_config import logger


class CompanyService:
    """Handles company profile CRUD operations."""

    def __init__(self, db):
        self.db = db
        self.collection = db[Config.COMPANIES_COLLECTION] if db is not None else None

    def get_company(self, owner_id: str) -> Optional[Company]:
        """Get the company profile for a given owner user."""
        if self.collection is None:
            return None
        try:
            data = self.collection.find_one({"owner_id": owner_id})
            return Company.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Error fetching company: {e}")
            return None

    def upsert_company(
        self, owner_id: str, data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Company], Optional[str]]:
        """Create or update the company profile for an owner."""
        if self.collection is None:
            return False, None, "Database not available"
        if not data.get("name", "").strip():
            return False, None, "Company name is required"
        try:
            protected = ["_id", "owner_id", "created_at"]
            for f in protected:
                data.pop(f, None)
            data["owner_id"] = owner_id
            data["updated_at"] = datetime.utcnow()

            existing = self.collection.find_one({"owner_id": owner_id})
            if existing:
                self.collection.update_one({"owner_id": owner_id}, {"$set": data})
                updated = self.collection.find_one({"owner_id": owner_id})
                company = Company.from_dict(updated)  # type: ignore
            else:
                data["created_at"] = datetime.utcnow()
                result = self.collection.insert_one(data)
                created = self.collection.find_one({"_id": result.inserted_id})
                company = Company.from_dict(created)  # type: ignore

            logger.info(f"Company profile upserted for owner {owner_id}")
            return True, company, None
        except Exception as e:
            logger.error(f"Error upserting company: {e}")
            return False, None, "Failed to save company profile"


# Singleton — initialized in app.py
company_service = None
