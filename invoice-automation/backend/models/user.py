"""User model and related enums."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    APPROVER = "approver"
    SUBMITTER = "submitter"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User:
    """User model with authentication and authorization."""
    
    def __init__(
        self,
        email: str,
        name: str,
        password_hash: str,
        roles: List[str] = None,
        status: str = UserStatus.ACTIVE,
        department: Optional[str] = None,
        _id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None,
        failed_login_attempts: int = 0
    ):
        self._id = _id
        self.email = email.lower().strip()
        self.name = name.strip()
        self.password_hash = password_hash
        self.roles = roles or [UserRole.SUBMITTER]
        self.status = status
        self.department = department
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_login = last_login
        self.failed_login_attempts = failed_login_attempts
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary for storage/serialization."""
        data = {
            "email": self.email,
            "name": self.name,
            "roles": self.roles,
            "status": self.status,
            "department": self.department,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "failed_login_attempts": self.failed_login_attempts
        }
        if include_password:
            data["password_hash"] = self.password_hash
        if self._id:
            data["_id"] = self._id
        return data
    
    def to_json(self) -> Dict[str, Any]:
        """Convert user to JSON-safe dictionary (no password, formatted dates)."""
        return {
            "id": str(self._id) if self._id else None,
            "email": self.email,
            "name": self.name,
            "roles": self.roles,
            "status": self.status,
            "department": self.department,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create User instance from dictionary."""
        return User(
            _id=str(data.get("_id")) if data.get("_id") else None,
            email=data["email"],
            name=data["name"],
            password_hash=data["password_hash"],
            roles=data.get("roles", [UserRole.SUBMITTER]),
            status=data.get("status", UserStatus.ACTIVE),
            department=data.get("department"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_login=data.get("last_login"),
            failed_login_attempts=data.get("failed_login_attempts", 0)
        )
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return UserRole.ADMIN in self.roles
    
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE
    
    def can_approve(self) -> bool:
        """Check if user can approve invoices."""
        return self.has_any_role([UserRole.ADMIN, UserRole.APPROVER])
    
    def can_submit(self) -> bool:
        """Check if user can submit invoices."""
        return self.has_any_role([UserRole.ADMIN, UserRole.APPROVER, UserRole.SUBMITTER])
