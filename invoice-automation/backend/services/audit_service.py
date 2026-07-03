"""Audit logging service for tracking all system actions."""
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import Config  # type: ignore
from logger_config import logger


class AuditAction:
    """Standard audit actions."""
    # Invoice actions
    INVOICE_CREATED = "invoice_created"
    INVOICE_UPDATED = "invoice_updated"
    INVOICE_DELETED = "invoice_deleted"
    INVOICE_SUBMITTED = "invoice_submitted"
    INVOICE_APPROVED = "invoice_approved"
    INVOICE_REJECTED = "invoice_rejected"
    INVOICE_PAID = "invoice_paid"
    INVOICE_CANCELLED = "invoice_cancelled"
    
    # User actions
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PASSWORD_CHANGED = "user_password_changed"
    USER_UPDATED = "user_updated"
    USER_LOCKED = "user_locked"
    
    # Vendor actions
    VENDOR_CREATED = "vendor_created"
    VENDOR_UPDATED = "vendor_updated"
    VENDOR_DEACTIVATED = "vendor_deactivated"
    VENDOR_BLOCKED = "vendor_blocked"


class AuditService:
    """Service for logging and querying audit trails."""
    
    def __init__(self, db):
        self.db = db
        self.audit_collection = db[Config.AUDIT_LOG_COLLECTION] if db is not None else None
    
    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Log an audit event."""
        if not self.audit_collection:
            logger.warning("Audit collection not available")
            return False
        
        try:
            audit_entry = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "details": details or {},
                "changes": changes or {},
                "ip_address": ip_address
            }
            
            self.audit_collection.insert_one(audit_entry)
            logger.debug(f"Audit logged: {action} on {entity_type}:{entity_id} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
            return False
    
    def log_invoice_action(
        self,
        action: str,
        invoice_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log invoice-related action."""
        return self.log(
            action=action,
            entity_type="invoice",
            entity_id=invoice_id,
            user_id=user_id,
            details=details,
            changes=changes
        )
    
    def log_user_action(
        self,
        action: str,
        user_id: str,
        actor_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Log user-related action."""
        return self.log(
            action=action,
            entity_type="user",
            entity_id=user_id,
            user_id=actor_id or user_id,
            details=details,
            ip_address=ip_address
        )
    
    def log_vendor_action(
        self,
        action: str,
        vendor_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log vendor-related action."""
        return self.log(
            action=action,
            entity_type="vendor",
            entity_id=vendor_id,
            user_id=user_id,
            details=details
        )
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit history for a specific entity."""
        if not self.audit_collection:
            return []
        
        try:
            query = {
                "entity_type": entity_type,
                "entity_id": entity_id
            }
            
            history = self.audit_collection.find(query).sort("timestamp", -1).limit(limit)
            return [self._format_audit_entry(entry) for entry in history]
            
        except Exception as e:
            logger.error(f"Error fetching audit history: {e}")
            return []
    
    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get activity log for a specific user."""
        if not self.audit_collection:
            return []
        
        try:
            query = {"user_id": user_id}
            
            if start_date or end_date:
                timestamp_query = {}
                if start_date:
                    timestamp_query["$gte"] = start_date
                if end_date:
                    timestamp_query["$lte"] = end_date
                if timestamp_query:
                    query["timestamp"] = timestamp_query
            
            activity = self.audit_collection.find(query).sort("timestamp", -1).limit(limit)
            return [self._format_audit_entry(entry) for entry in activity]
            
        except Exception as e:
            logger.error(f"Error fetching user activity: {e}")
            return []
    
    def get_recent_activity(
        self,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent system activity."""
        if not self.audit_collection:
            return []
        
        try:
            query = {}
            if entity_type:
                query["entity_type"] = entity_type
            if action:
                query["action"] = action
            
            activity = self.audit_collection.find(query).sort("timestamp", -1).limit(limit)
            return [self._format_audit_entry(entry) for entry in activity]
            
        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")
            return []
    
    def search_audit_log(
        self,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Search audit log with multiple filters."""
        if not self.audit_collection:
            return []
        
        try:
            query = {}
            
            if user_id:
                query["user_id"] = user_id
            if entity_type:
                query["entity_type"] = entity_type
            if action:
                query["action"] = action
            
            if start_date or end_date:
                timestamp_query = {}
                if start_date:
                    timestamp_query["$gte"] = start_date
                if end_date:
                    timestamp_query["$lte"] = end_date
                if timestamp_query:
                    query["timestamp"] = timestamp_query
            
            results = self.audit_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            return [self._format_audit_entry(entry) for entry in results]
            
        except Exception as e:
            logger.error(f"Error searching audit log: {e}")
            return []
    
    def _format_audit_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Format audit entry for JSON response."""
        return {
            "id": str(entry["_id"]),
            "action": entry["action"],
            "entity_type": entry["entity_type"],
            "entity_id": entry["entity_id"],
            "user_id": entry["user_id"],
            "timestamp": entry["timestamp"].isoformat() if entry.get("timestamp") else None,
            "details": entry.get("details", {}),
            "changes": entry.get("changes", {}),
            "ip_address": entry.get("ip_address")
        }


# Singleton instance (will be initialized in app.py)
audit_service = None
