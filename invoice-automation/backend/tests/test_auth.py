"""Tests for authentication system."""
import pytest
from services.auth_service import AuthService
from models.user import UserRole, UserStatus

def test_password_hashing():
    """Test password hashing and verification."""
    from db import db_manager
    auth = AuthService(db_manager.db)
    
    password = "TestPassword123"
    hashed = auth.hash_password(password)
    
    assert hashed != password
    assert auth.verify_password(password, hashed)
    assert not auth.verify_password("WrongPassword", hashed)

def test_email_validation():
    """Test email format validation."""
    from db import db_manager
    auth = AuthService(db_manager.db)
    
    # Valid emails
    valid, _ = auth.validate_email_format("user@example.com")
    assert valid
    
    valid, _ = auth.validate_email_format("test.user+tag@company.co.uk")
    assert valid
    
    # Invalid emails
    valid, _ = auth.validate_email_format("notanemail")
    assert not valid
    
    valid, _ = auth.validate_email_format("@example.com")
    assert not valid

def test_password_strength_validation():
    """Test password strength requirements."""
    from db import db_manager
    auth = AuthService(db_manager.db)
    
    # Too short
    valid, error = auth.validate_password_strength("Pass1")
    assert not valid
    assert "8 characters" in error
    
    # No uppercase
    valid, error = auth.validate_password_strength("password123")
    assert not valid
    assert "uppercase" in error
    
    # No lowercase
    valid, error = auth.validate_password_strength("PASSWORD123")
    assert not valid
    assert "lowercase" in error
    
    # No digit
    valid, error = auth.validate_password_strength("Password")
    assert not valid
    assert "digit" in error
    
    # Valid password
    valid, error = auth.validate_password_strength("ValidPass123")
    assert valid
    assert error is None

def test_token_generation_and_verification():
    """Test JWT token generation and verification."""
    from db import db_manager
    from models.user import User
    
    auth = AuthService(db_manager.db)
    
    # Create a test user object
    user = User(
        _id="test123",
        email="test@example.com",
        name="Test User",
        password_hash="dummy",
        roles=[UserRole.SUBMITTER]
    )
    
    # Generate token
    token = auth.generate_access_token(user)
    assert token is not None
    assert len(token) > 0
    
    # Verify token
    valid, payload, error = auth.verify_token(token)
    assert valid
    assert error is None
    assert payload["user_id"] == "test123"
    assert payload["email"] == "test@example.com"
    assert payload["type"] == "access"
    assert UserRole.SUBMITTER in payload["roles"]

def test_user_model_permissions():
    """Test user permission methods."""
    from models.user import User, UserRole
    
    # Submitter
    submitter = User(
        email="submitter@example.com",
        name="Submitter",
        password_hash="dummy",
        roles=[UserRole.SUBMITTER]
    )
    assert submitter.can_submit()
    assert not submitter.can_approve()
    assert not submitter.is_admin()
    assert submitter.has_role(UserRole.SUBMITTER)
    
    # Approver
    approver = User(
        email="approver@example.com",
        name="Approver",
        password_hash="dummy",
        roles=[UserRole.APPROVER]
    )
    assert approver.can_submit()
    assert approver.can_approve()
    assert not approver.is_admin()
    
    # Admin
    admin = User(
        email="admin@example.com",
        name="Admin",
        password_hash="dummy",
        roles=[UserRole.ADMIN, UserRole.APPROVER, UserRole.SUBMITTER]
    )
    assert admin.can_submit()
    assert admin.can_approve()
    assert admin.is_admin()
    assert admin.has_any_role([UserRole.ADMIN, UserRole.VIEWER])
