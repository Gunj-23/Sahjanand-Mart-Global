"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from sahjanand_mart.app import create_app
from sahjanand_mart.config import TestingConfig
from sahjanand_mart.db import init_db, get_db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    class TestConfig(TestingConfig):
        DATABASE = db_path
    
    app = create_app(TestConfig)
    
    with app.app_context():
        init_db(app)
        
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth(client):
    """Authentication helper."""
    class AuthActions:
        def __init__(self, client):
            self._client = client
        
        def login(self, username='admin', password='admin'):
            return self._client.post(
                '/login',
                data={'username': username, 'password': password}
            )
        
        def logout(self):
            return self._client.get('/logout')
    
    return AuthActions(client)