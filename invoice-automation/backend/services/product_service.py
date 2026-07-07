"""Product/Service management service."""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from config import Config  # type: ignore
from models.product import Product  # type: ignore
from logger_config import logger


class ProductService:
    """Handles product and service CRUD operations."""

    def __init__(self, db):
        self.db = db
        self.collection = db[Config.PRODUCTS_COLLECTION] if db is not None else None

    def create_product(
        self,
        name: str,
        user_id: str,
        sku: Optional[str] = None,
        description: Optional[str] = None,
        unit_price: float = 0.0,
        tax_rate: float = 0.0,
        category: Optional[str] = None,
    ) -> Tuple[bool, Optional[Product], Optional[str]]:
        """Create a new product or service."""
        if self.collection is None:
            return False, None, "Database not available"
        if not name or not name.strip():
            return False, None, "Product name is required"
        try:
            product = Product(
                name=name.strip(),
                sku=sku,
                description=description,
                unit_price=float(unit_price),
                tax_rate=float(tax_rate),
                category=category,
                created_by=user_id,
            )
            result = self.collection.insert_one(product.to_dict())
            product._id = str(result.inserted_id)
            logger.info(f"Product created: {product.name} by user {user_id}")
            return True, product, None
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return False, None, "Failed to create product"

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        if self.collection is None:
            return None
        try:
            from bson import ObjectId  # type: ignore
            data = self.collection.find_one({"_id": ObjectId(product_id)})
            return Product.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Error fetching product: {e}")
            return None

    def list_products(
        self,
        search: Optional[str] = None,
        active_only: bool = True,
        limit: int = 200,
        skip: int = 0,
    ) -> List[Product]:
        if self.collection is None:
            return []
        try:
            query: Dict[str, Any] = {}
            if active_only:
                query["is_active"] = True
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"sku": {"$regex": search, "$options": "i"}},
                ]
            data = self.collection.find(query).sort("name", 1).skip(skip).limit(limit)
            return [Product.from_dict(d) for d in data]
        except Exception as e:
            logger.error(f"Error listing products: {e}")
            return []

    def count_products(self) -> int:
        if self.collection is None:
            return 0
        try:
            return self.collection.count_documents({"is_active": True})
        except Exception:
            return 0

    def update_product(
        self, product_id: str, updates: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        if self.collection is None:
            return False, "Database not available"
        try:
            from bson import ObjectId  # type: ignore
            protected = ["_id", "created_at", "created_by"]
            for f in protected:
                updates.pop(f, None)
            updates["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(product_id)}, {"$set": updates}
            )
            if result.matched_count == 0:
                return False, "Product not found"
            return True, None
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False, "Failed to update product"

    def delete_product(self, product_id: str) -> Tuple[bool, Optional[str]]:
        """Soft-delete by marking inactive."""
        return self.update_product(product_id, {"is_active": False})


# Singleton — initialized in app.py
product_service = None
