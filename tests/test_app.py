"""Test application factory and configuration."""

import pytest
from sahjanand_mart.app import create_app
from sahjanand_mart.config import TestingConfig

def test_config():
    """Test that the app is created with test config."""
    assert not create_app().testing
    assert create_app(TestingConfig).testing

def test_hello(client):
    """Test that the app redirects to login when not authenticated."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location