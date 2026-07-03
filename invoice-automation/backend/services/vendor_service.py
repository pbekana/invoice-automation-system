"""Vendor management service."""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from config import Config  # type: ignore
from models.vendor import Vendor, VendorStatus  # type: ignore
from logger_config import logger


class VendorService:
    """Handles vendor CRUD operations and matching."""
    
    def __init__(self, db):
        self.db = db
        self.vendors_collection = db[Config.VENDORS_COLLECTION] if db is not None else None
    
    def create_vendor(
        self,
        name: str,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
        default_category: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[Vendor], Optional[str]]:
        """Create a new vendor."""
        if not self.vendors_collection:
            return False, None, "Database not available"
        
        if not name or not name.strip():
            return False, None, "Vendor name is required"
        
        # Normalize name for deduplication
        normalized_name = Vendor.normalize_name(name)
        
        # Check for duplicate
        existing = self.vendors_collection.find_one({"normalized_name": normalized_name})
        if existing:
            return False, None, f"Vendor already exists: {existing['name']}"
        
        try:
            vendor = Vendor(
                name=name.strip(),
                normalized_name=normalized_name,
                email=email,
                phone=phone,
                address=address,
                tax_id=tax_id,
                payment_terms=payment_terms,
                default_category=default_category,
                notes=notes,
                created_by=user_id
            )
            
            result = self.vendors_collection.insert_one(vendor.to_dict())
            vendor._id = str(result.inserted_id)
            
            logger.info(f"Vendor created: {vendor.name} by user {user_id}")
            return True, vendor, None
            
        except Exception as e:
            logger.error(f"Error creating vendor: {e}")
            return False, None, "Failed to create vendor"
    
    def get_vendor_by_id(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID."""
        if not self.vendors_collection:
            return None
        
        try:
            from bson import ObjectId  # type: ignore
            vendor_data = self.vendors_collection.find_one({"_id": ObjectId(vendor_id)})
            if vendor_data:
                return Vendor.from_dict(vendor_data)
        except Exception as e:
            logger.error(f"Error fetching vendor: {e}")
        
        return None
    
    def find_vendor_by_name(self, name: str, fuzzy: bool = True) -> Optional[Vendor]:
        """Find vendor by name (exact or fuzzy match)."""
        if not self.vendors_collection or not name:
            return None
        
        try:
            # Try exact normalized match first
            normalized = Vendor.normalize_name(name)
            vendor_data = self.vendors_collection.find_one({"normalized_name": normalized})
            
            if vendor_data:
                return Vendor.from_dict(vendor_data)
            
            if fuzzy:
                # Try case-insensitive partial match
                vendor_data = self.vendors_collection.find_one({
                    "name": {"$regex": re.escape(name), "$options": "i"}
                })
                if vendor_data:
                    return Vendor.from_dict(vendor_data)
            
        except Exception as e:
            logger.error(f"Error finding vendor by name: {e}")
        
        return None
    
    def get_or_create_vendor(
        self,
        name: str,
        user_id: str,
        default_category: Optional[str] = None
    ) -> Tuple[bool, Optional[Vendor], bool]:
        """Get existing vendor or create new one. Returns (success, vendor, was_created)."""
        # Try to find existing
        existing = self.find_vendor_by_name(name)
        if existing:
            return True, existing, False
        
        # Create new
        success, vendor, error = self.create_vendor(
            name=name,
            user_id=user_id,
            default_category=default_category
        )
        
        if success:
            return True, vendor, True
        else:
            logger.warning(f"Failed to create vendor {name}: {error}")
            return False, None, False
    
    def update_vendor(
        self,
        vendor_id: str,
        updates: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Update vendor information."""
        if not self.vendors_collection:
            return False, "Database not available"
        
        try:
            from bson import ObjectId  # type: ignore
            
            # Don't allow updating certain fields
            protected_fields = ["_id", "normalized_name", "created_at", "created_by"]
            for field in protected_fields:
                updates.pop(field, None)
            
            # Update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            # If name is being updated, update normalized_name too
            if "name" in updates:
                updates["normalized_name"] = Vendor.normalize_name(updates["name"])
            
            result = self.vendors_collection.update_one(
                {"_id": ObjectId(vendor_id)},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Vendor not found"
            
            logger.info(f"Vendor updated: {vendor_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error updating vendor: {e}")
            return False, "Failed to update vendor"
    
    def list_vendors(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Vendor]:
        """List vendors with optional filtering."""
        if not self.vendors_collection:
            return []
        
        try:
            query = {}
            
            if status:
                query["status"] = status
            
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"normalized_name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}}
                ]
            
            vendors_data = self.vendors_collection.find(query).sort("name", 1).skip(skip).limit(limit)
            return [Vendor.from_dict(v) for v in vendors_data]
            
        except Exception as e:
            logger.error(f"Error listing vendors: {e}")
            return []
    
    def count_vendors(self, status: Optional[str] = None) -> int:
        """Count vendors."""
        if not self.vendors_collection:
            return 0
        
        try:
            query = {"status": status} if status else {}
            return self.vendors_collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting vendors: {e}")
            return 0
    
    def deactivate_vendor(self, vendor_id: str) -> Tuple[bool, Optional[str]]:
        """Deactivate a vendor."""
        return self.update_vendor(vendor_id, {"status": VendorStatus.INACTIVE})
    
    def block_vendor(self, vendor_id: str, reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Block a vendor."""
        updates = {"status": VendorStatus.BLOCKED}
        if reason:
            updates["notes"] = reason
        return self.update_vendor(vendor_id, updates)


# Module import support
import re

# Singleton instance (will be initialized in app.py)
vendor_service = None
