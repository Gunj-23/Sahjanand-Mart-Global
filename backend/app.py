from flask import Flask, render_template, request, jsonify, redirect, url_for
from db import init_db, get_db, close_db
from datetime import datetime, timedelta, date
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(basedir, '../templates'),
            static_folder=os.path.join(basedir, '../backend/static'))

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

with app.app_context():
    init_db(app)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/inventory')
def inventory():
    db = get_db()
    products = db.execute(text('''
        SELECT *, 
        CASE 
            WHEN expiry_date IS NULL THEN 0
            WHEN expiry_date < CURRENT_DATE THEN 1
            ELSE 0
        END as is_expired,
        CASE
            WHEN expiry_date IS NULL THEN 0
            WHEN expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days' THEN 1
            ELSE 0
        END as is_expiring_soon
        FROM products
    ''')).fetchall()

    product_list = []
    for product in products:
        product_dict = dict(product._mapping)
        if product_dict['expiry_date']:
            try:
                product_dict['expiry_date'] = product_dict['expiry_date']
            except (ValueError, TypeError):
                product_dict['expiry_date'] = None
        product_list.append(product_dict)

    return render_template('inventory.html', products=product_list)

@app.route('/billing')
def billing():
    db = get_db()
    products = db.execute(text('SELECT * FROM products WHERE stock > 0')).fetchall()
    return render_template('billing.html', products=products)

@app.route('/api/products', methods=['GET', 'POST'])
def products():
    db = get_db()

    if request.method == 'GET':
        barcode = request.args.get('barcode')
        search = request.args.get('search')

        if barcode:
            barcode = barcode.strip()
            product = db.execute(text('SELECT * FROM products WHERE barcode = :barcode'), {'barcode': barcode}).fetchone()
            if product:
                return jsonify({'success': True, 'product': dict(product._mapping), 'message': 'Product found'})
            else:
                return jsonify({'success': False, 'error': 'Product not found', 'barcode': barcode}), 404
        elif search:
            products = db.execute(text('SELECT * FROM products WHERE name ILIKE :search'), {'search': f'%{search}%'}).fetchall()
        else:
            products = db.execute(text('SELECT * FROM products')).fetchall()

        return jsonify([dict(row._mapping) for row in products])

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        required_fields = ['name', 'price', 'stock']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        try:
            db.execute(text('''
                INSERT INTO products (name, price, stock, discount, barcode, category, expiry_date)
                VALUES (:name, :price, :stock, :discount, :barcode, :category, :expiry_date)
            '''), data)
            db.commit()
            return jsonify({'success': True})
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def handle_scan():
    data = request.get_json()
    if not data or 'barcode' not in data:
        return jsonify({'success': False, 'error': 'No barcode provided'}), 400

    barcode = data['barcode'].strip()
    db = get_db()

    product = db.execute(text('SELECT * FROM products WHERE barcode = :barcode'), {'barcode': barcode}).fetchone()
    if product:
        return jsonify({'success': True, 'product': dict(product._mapping), 'message': 'Product found by barcode'})

    try:
        product_id = int(barcode)
        product = db.execute(text('SELECT * FROM products WHERE id = :id'), {'id': product_id}).fetchone()
        if product:
            return jsonify({'success': True, 'product': dict(product._mapping), 'message': 'Product found by ID'})
    except ValueError:
        pass

    return jsonify({'success': False, 'error': 'Product not found', 'barcode': barcode}), 404

@app.route('/api/sale', methods=['POST'])
def create_sale():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    required_fields = ['items', 'total', 'payment_mode']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    db = get_db()
    try:
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.05

        sale_result = db.execute(text('''
            INSERT INTO sales (subtotal, tax, total_amount, date, payment_mode)
            VALUES (:subtotal, :tax, :total_amount, :date, :payment_mode)
            RETURNING id
        '''), {
            'subtotal': subtotal,
            'tax': tax,
            'total_amount': data['total'],
            'date': datetime.now(),
            'payment_mode': data['payment_mode']
        })
        sale_id = sale_result.scalar()

        for item in data['items']:
            product = db.execute(text('SELECT * FROM products WHERE id = :id'), {'id': item['id']}).fetchone()
            if not product:
                db.rollback()
                return jsonify({'success': False, 'error': f'Product ID {item["id"]} not found'}), 404

            if product.stock < item['quantity']:
                db.rollback()
                return jsonify({'success': False, 'error': f'Not enough stock for {product.name}'}), 400

            db.execute(text('''
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (:sale_id, :product_id, :quantity, :price)
            '''), {
                'sale_id': sale_id,
                'product_id': item['id'],
                'quantity': item['quantity'],
                'price': item['price']
            })

            db.execute(text('UPDATE products SET stock = stock - :quantity WHERE id = :id'), {
                'quantity': item['quantity'],
                'id': item['id']
            })

        db.commit()

        return jsonify({
            'success': True,
            'sale_id': sale_id,
            'sale': {
                'id': sale_id,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'items': data['items'],
                'subtotal': subtotal,
                'tax': tax,
                'total_amount': data['total'],
                'payment_mode': data['payment_mode']
            }
        })
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def product_operations(product_id):
    db = get_db()
    if request.method == 'PUT':
        data = request.get_json()
        try:
            db.execute(text('''
                UPDATE products SET name=:name, price=:price, stock=:stock, discount=:discount,
                barcode=:barcode, category=:category, expiry_date=:expiry_date WHERE id=:id
            '''), {
                **data,
                'id': product_id
            })
            db.commit()
            return jsonify({'success': True})
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.execute(text('DELETE FROM products WHERE id = :id'), {'id': product_id})
            db.commit()
            return jsonify({'success': True})
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    db = get_db()
    today_sales = db.execute(text('''
        SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE DATE(date) = CURRENT_DATE
    ''')).scalar()
    total_products = db.execute(text('SELECT COUNT(*) FROM products')).scalar()
    low_stock = db.execute(text('SELECT COUNT(*) FROM products WHERE stock < 10')).scalar()

    return jsonify({
        'today_sales': today_sales,
        'total_products': total_products,
        'low_stock': low_stock
    })

@app.route('/api/sales-data')
def sales_data():
    db = get_db()
    sales = db.execute(text('''
        SELECT DATE(date) as day, SUM(total_amount) as total
        FROM sales WHERE date >= CURRENT_DATE - INTERVAL '6 days'
        GROUP BY DATE(date)
        ORDER BY DATE(date)
    ''')).fetchall()

    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    sales_dict = {row._mapping['day'].strftime('%Y-%m-%d'): row._mapping['total'] for row in sales}

    return jsonify({
        'labels': dates,
        'values': [sales_dict.get(date, 0) for date in dates]
    })

@app.route('/api/inventory-data')
def inventory_data():
    db = get_db()
    data = db.execute(text('''
        SELECT category, SUM(stock) as total FROM products WHERE category IS NOT NULL GROUP BY category
    ''')).fetchall()

    return jsonify({
        'labels': [row._mapping['category'] for row in data],
        'values': [row._mapping['total'] for row in data]
    })

@app.route('/api/payment-data')
def payment_data():
    db = get_db()
    data = db.execute(text('''
        SELECT payment_mode, SUM(total_amount) as total FROM sales GROUP BY payment_mode
    ''')).fetchall()

    return jsonify({
        'labels': [row._mapping['payment_mode'].capitalize() for row in data],
        'values': [row._mapping['total'] for row in data]
    })

@app.route('/api/products/low-stock')
def low_stock_products():
    db = get_db()
    products = db.execute(text('''
        SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC
    ''')).fetchall()
    return jsonify([dict(product._mapping) for product in products])

if __name__ == '__main__':
    app.run(debug=True)
