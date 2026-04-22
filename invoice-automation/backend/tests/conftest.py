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
