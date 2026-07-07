import pytest
from app import app as flask_app
from db import DatabaseManager
from unittest.mock import MagicMock

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db_manager(monkeypatch):
    mock = MagicMock(spec=DatabaseManager)
    monkeypatch.setattr("app.db_manager", mock)
    return mock

@pytest.fixture
def mongo_db():
    manager = DatabaseManager(db_name="invoice_db_test")
    db = manager.db
    # Clean database collections before test runs
    for name in db.list_collection_names():
        if not name.startswith("system."):
            db[name].delete_many({})
    yield db
    # Drop the database after the test
    manager.client.drop_database("invoice_db_test")

@pytest.fixture
def auth_headers(monkeypatch):
    from services.auth_service import AuthService
    from models.user import User, UserRole
    
    # Mock verify_token
    monkeypatch.setattr(AuthService, "verify_token", lambda self, token: (True, {"user_id": "test_user_id", "email": "test@example.com", "roles": [UserRole.ADMIN]}, None))
    
    # Mock get_user_by_id
    mock_user = User(
        _id="test_user_id",
        email="test@example.com",
        name="Test User",
        password_hash="dummy",
        roles=[UserRole.ADMIN]
    )
    monkeypatch.setattr(AuthService, "get_user_by_id", lambda self, user_id: mock_user)
    
    return {"Authorization": "Bearer dummy_token"}


