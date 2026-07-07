"""Customer management service."""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from config import Config  # type: ignore
from models.customer import Customer, CustomerStatus  # type: ignore
from logger_config import logger


class CustomerService:
    """Handles customer CRUD operations."""

    def __init__(self, db):
        self.db = db
        self.collection = db[Config.CUSTOMERS_COLLECTION] if db is not None else None

    def create_customer(
        self,
        name: str,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        billing_address: Optional[str] = None,
        shipping_address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
    ) -> Tuple[bool, Optional[Customer], Optional[str]]:
        """Create a new customer."""
        if self.collection is None:
            return False, None, "Database not available"
        if not name or not name.strip():
            return False, None, "Customer name is required"

        try:
            customer = Customer(
                name=name.strip(),
                email=email,
                phone=phone,
                billing_address=billing_address,
                shipping_address=shipping_address,
                tax_id=tax_id,
                payment_terms=payment_terms,
                currency=currency,
                notes=notes,
                created_by=user_id,
            )
            result = self.collection.insert_one(customer.to_dict())
            customer._id = str(result.inserted_id)
            logger.info(f"Customer created: {customer.name} by user {user_id}")
            return True, customer, None
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return False, None, "Failed to create customer"

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        if self.collection is None:
            return None
        try:
            from bson import ObjectId  # type: ignore
            data = self.collection.find_one({"_id": ObjectId(customer_id)})
            return Customer.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Error fetching customer: {e}")
            return None

    def list_customers(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Customer]:
        """List customers with optional filtering."""
        if self.collection is None:
            return []
        try:
            query: Dict[str, Any] = {}
            if status:
                query["status"] = status
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                ]
            data = self.collection.find(query).sort("name", 1).skip(skip).limit(limit)
            return [Customer.from_dict(d) for d in data]
        except Exception as e:
            logger.error(f"Error listing customers: {e}")
            return []

    def count_customers(self) -> int:
        if self.collection is None:
            return 0
        try:
            return self.collection.count_documents({})
        except Exception:
            return 0

    def update_customer(
        self, customer_id: str, updates: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Update customer information."""
        if self.collection is None:
            return False, "Database not available"
        try:
            from bson import ObjectId  # type: ignore
            protected = ["_id", "created_at", "created_by"]
            for f in protected:
                updates.pop(f, None)
            updates["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(customer_id)}, {"$set": updates}
            )
            if result.matched_count == 0:
                return False, "Customer not found"
            logger.info(f"Customer updated: {customer_id}")
            return True, None
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            return False, "Failed to update customer"

    def delete_customer(self, customer_id: str) -> Tuple[bool, Optional[str]]:
        """Soft-delete a customer by setting status to inactive."""
        return self.update_customer(customer_id, {"status": CustomerStatus.INACTIVE})


# Singleton — initialized in app.py
customer_service = None
