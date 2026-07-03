"""Authentication and authorization service."""
import bcrypt  # type: ignore
import jwt  # type: ignore
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from email_validator import validate_email, EmailNotValidError  # type: ignore

from config import Config  # type: ignore
from models.user import User, UserRole, UserStatus  # type: ignore
from logger_config import logger


class AuthService:
    """Handles user authentication, token generation, and password management."""
    
    def __init__(self, db):
        self.db = db
        self.users_collection = db[Config.USERS_COLLECTION] if db is not None else None
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=Config.BCRYPT_LOG_ROUNDS)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def validate_email_format(self, email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format."""
        try:
            valid = validate_email(email, check_deliverability=False)
            return True, valid.normalized
        except EmailNotValidError as e:
            return False, str(e)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """Validate password meets security requirements."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        return True, None
    
    def register_user(
        self,
        email: str,
        name: str,
        password: str,
        roles: Optional[list] = None,
        department: Optional[str] = None
    ) -> Tuple[bool, Optional[User], Optional[str]]:
        """Register a new user."""
        if not self.users_collection:
            return False, None, "Database not available"
        
        # Validate email
        email_valid, email_or_error = self.validate_email_format(email)
        if not email_valid:
            return False, None, f"Invalid email: {email_or_error}"
        email = email_or_error
        
        # Check if user already exists
        if self.users_collection.find_one({"email": email}):
            return False, None, "User with this email already exists"
        
        # Validate password
        password_valid, password_error = self.validate_password_strength(password)
        if not password_valid:
            return False, None, password_error
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            name=name,
            password_hash=password_hash,
            roles=roles or [UserRole.SUBMITTER],
            department=department
        )
        
        try:
            result = self.users_collection.insert_one(user.to_dict(include_password=True))
            user._id = str(result.inserted_id)
            logger.info(f"User registered: {email}")
            return True, user, None
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return False, None, "Failed to create user"
    
    def authenticate(self, email: str, password: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """Authenticate user with email and password."""
        if not self.users_collection:
            return False, None, "Database not available"
        
        try:
            # Find user
            user_data = self.users_collection.find_one({"email": email.lower().strip()})
            if not user_data:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return False, None, "Invalid email or password"
            
            user = User.from_dict(user_data)
            
            # Check if account is locked
            if user.status == UserStatus.LOCKED:
                return False, None, "Account is locked. Contact administrator."
            
            # Check if account is inactive
            if user.status == UserStatus.INACTIVE:
                return False, None, "Account is inactive"
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Increment failed attempts
                self.users_collection.update_one(
                    {"_id": user_data["_id"]},
                    {
                        "$inc": {"failed_login_attempts": 1},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts + 1 >= 5:
                    self.users_collection.update_one(
                        {"_id": user_data["_id"]},
                        {"$set": {"status": UserStatus.LOCKED, "updated_at": datetime.utcnow()}}
                    )
                    logger.warning(f"Account locked due to failed attempts: {email}")
                    return False, None, "Account locked due to multiple failed login attempts"
                
                logger.warning(f"Failed login attempt for user: {email}")
                return False, None, "Invalid email or password"
            
            # Successful login - reset failed attempts and update last login
            self.users_collection.update_one(
                {"_id": user_data["_id"]},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "failed_login_attempts": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"User authenticated: {email}")
            return True, user, None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, None, "Authentication failed"
    
    def generate_access_token(self, user: User) -> str:
        """Generate JWT access token."""
        payload = {
            "user_id": str(user._id),
            "email": user.email,
            "roles": user.roles,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    
    def generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token."""
        payload = {
            "user_id": str(user._id),
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        if not self.users_collection:
            return None
        
        try:
            from bson import ObjectId  # type: ignore
            user_data = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User.from_dict(user_data)
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
        
        return None
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Generate new access token from refresh token."""
        valid, payload, error = self.verify_token(refresh_token)
        
        if not valid:
            return False, None, error
        
        if payload.get("type") != "refresh":
            return False, None, "Invalid token type"
        
        user = self.get_user_by_id(payload["user_id"])
        if not user or not user.is_active():
            return False, None, "User not found or inactive"
        
        new_access_token = self.generate_access_token(user)
        return True, new_access_token, None
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """Change user password."""
        if not self.users_collection:
            return False, "Database not available"
        
        try:
            from bson import ObjectId  # type: ignore
            user_data = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_data:
                return False, "User not found"
            
            user = User.from_dict(user_data)
            
            # Verify old password
            if not self.verify_password(old_password, user.password_hash):
                return False, "Current password is incorrect"
            
            # Validate new password
            password_valid, password_error = self.validate_password_strength(new_password)
            if not password_valid:
                return False, password_error
            
            # Hash and update
            new_password_hash = self.hash_password(new_password)
            self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Password changed for user: {user.email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, "Failed to change password"


# Singleton instance (will be initialized in app.py with db connection)
auth_service = None
