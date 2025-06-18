"""Test authentication functionality."""

import pytest
from flask import session
from sahjanand_mart.db import get_db

def test_register(client, app):
    """Test user registration."""
    # Test that registration page loads
    response = client.get('/login')
    assert response.status_code == 200
    
    # Test successful registration
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass',
        'role': 'employee'
    })
    assert response.status_code == 302  # Redirect after successful registration
    
    # Test that user was created in database
    with app.app_context():
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', ('testuser',)).fetchone()
        assert user is not None

def test_login_logout(client, app):
    """Test login and logout functionality."""
    # First register a user
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass',
        'role': 'employee'
    })
    
    # Test login with correct credentials
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 302  # Redirect after successful login
    
    # Test that user is logged in
    with client.session_transaction() as sess:
        assert sess.get('username') == 'testuser'
    
    # Test logout
    response = client.get('/logout')
    assert response.status_code == 302
    
    # Test that user is logged out
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_login_required(client):
    """Test that login is required for protected routes."""
    protected_routes = ['/', '/inventory', '/billing', '/bill-history', '/gst-reports']
    
    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302
        assert '/login' in response.location