"""Test API endpoints."""

import pytest
import json
from sahjanand_mart.db import get_db

def test_products_api(client, app, auth):
    """Test products API endpoints."""
    # Login first
    auth.login()
    
    # Test GET products (should return empty list initially)
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    
    # Test POST new product
    product_data = {
        'name': 'Test Product',
        'price': 10.50,
        'stock': 100,
        'barcode': '1234567890',
        'category': 'Test Category'
    }
    
    response = client.post('/api/products', 
                          data=json.dumps(product_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'id' in data
    
    # Test GET products after adding one
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert data[0]['name'] == 'Test Product'

def test_scan_api(client, app, auth):
    """Test barcode scanning API."""
    auth.login()
    
    # First add a product
    with app.app_context():
        db = get_db()
        db.execute('''
            INSERT INTO products (name, price, stock, barcode)
            VALUES (?, ?, ?, ?)
        ''', ('Test Product', 10.50, 100, '1234567890'))
        db.commit()
    
    # Test scanning existing barcode
    response = client.post('/api/scan',
                          data=json.dumps({'barcode': '1234567890'}),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['product']['name'] == 'Test Product'
    
    # Test scanning non-existent barcode
    response = client.post('/api/scan',
                          data=json.dumps({'barcode': '9999999999'}),
                          content_type='application/json')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] is False

def test_sale_api(client, app, auth):
    """Test sales API."""
    auth.login()
    
    # First add a product
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO products (name, price, stock, barcode)
            VALUES (?, ?, ?, ?)
        ''', ('Test Product', 10.50, 100, '1234567890'))
        product_id = cursor.lastrowid
        db.commit()
    
    # Test creating a sale
    sale_data = {
        'items': [
            {'id': product_id, 'quantity': 2, 'price': 10.50}
        ],
        'total': 21.00,
        'payment_mode': 'cash'
    }
    
    response = client.post('/api/sale',
                          data=json.dumps(sale_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'sale_id' in data
    
    # Verify stock was updated
    with app.app_context():
        db = get_db()
        product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        assert product['stock'] == 98  # 100 - 2