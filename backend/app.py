from flask import Flask, render_template, request, jsonify, redirect, url_for
from db import init_db, get_db, close_db
from datetime import datetime, timedelta, date
import os
import sqlite3

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(basedir, '../templates'),
            static_folder=os.path.join(basedir, '../backend/static'))

app.config['DATABASE'] = os.path.join(basedir, '../database/sahjanand_mart.db')

# Ensure directories exist
os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

# Initialize database
with app.app_context():
    init_db(app)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/inventory')
def inventory():
    db = get_db()
    products = db.execute('''
        SELECT *, 
        CASE 
            WHEN expiry_date IS NULL THEN 0
            WHEN expiry_date < date('now') THEN 1
            ELSE 0
        END as is_expired,
        CASE
            WHEN expiry_date IS NULL THEN 0
            WHEN expiry_date BETWEEN date('now') AND date('now', '+30 days') THEN 1
            ELSE 0
        END as is_expiring_soon
        FROM products
    ''').fetchall()
    
    # Convert to dict and parse dates
    product_list = []
    for product in products:
        product_dict = dict(product)
        if product_dict['expiry_date']:
            try:
                product_dict['expiry_date'] = datetime.strptime(product_dict['expiry_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                product_dict['expiry_date'] = None
        product_list.append(product_dict)
    
    return render_template('inventory.html', products=product_list)

@app.route('/billing')
def billing():
    db = get_db()
    products = db.execute('SELECT * FROM products WHERE stock > 0').fetchall()
    return render_template('billing.html', products=products)

@app.route('/bill-history')
def bill_history():
    return render_template('bill_history.html')

@app.route('/api/products', methods=['GET', 'POST'])
def products():
    db = get_db()
    
    if request.method == 'GET':
        barcode = request.args.get('barcode')
        search = request.args.get('search')
        
        if barcode:
            barcode = barcode.strip()
            product = db.execute('SELECT * FROM products WHERE barcode = ?', (barcode,)).fetchone()
            if product:
                return jsonify({
                    'success': True,
                    'product': dict(product),
                    'message': 'Product found'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Product not found',
                    'barcode': barcode
                }), 404
        elif search:
            products = db.execute('SELECT * FROM products WHERE name LIKE ?', (f'%{search}%',)).fetchall()
        else:
            products = db.execute('SELECT * FROM products').fetchall()
        
        return jsonify([dict(product) for product in products])
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        required_fields = ['name', 'price', 'stock']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        try:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO products (name, price, stock, discount, barcode, category, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['price'],
                data['stock'],
                data.get('discount', 0),
                data.get('barcode'),
                data.get('category'),
                data.get('expiry_date')
            ))
            db.commit()
            return jsonify({'success': True, 'id': cursor.lastrowid})
        except sqlite3.Error as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def handle_scan():
    data = request.get_json()
    if not data or 'barcode' not in data:
        return jsonify({'success': False, 'error': 'No barcode provided'}), 400
    
    barcode = data['barcode'].strip()
    db = get_db()
    
    product = db.execute('SELECT * FROM products WHERE barcode = ?', (barcode,)).fetchone()
    if product:
        return jsonify({
            'success': True,
            'product': dict(product),
            'message': 'Product found by barcode'
        })
    
    try:
        product_id = int(barcode)
        product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            return jsonify({
                'success': True,
                'product': dict(product),
                'message': 'Product found by ID'
            })
    except ValueError:
        pass
    
    return jsonify({
        'success': False,
        'error': 'Product not found',
        'barcode': barcode
    }), 404

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
    cursor = db.cursor()
    
    try:
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.05
        
        cursor.execute(
            'INSERT INTO sales (subtotal, tax, total_amount, date, payment_mode) VALUES (?, ?, ?, ?, ?)',
            (subtotal, tax, data['total'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data['payment_mode'])
        )
        sale_id = cursor.lastrowid
        
        for item in data['items']:
            product = db.execute('SELECT * FROM products WHERE id = ?', (item['id'],)).fetchone()
            if not product:
                db.rollback()
                return jsonify({'success': False, 'error': f'Product ID {item["id"]} not found'}), 404
            
            if product['stock'] < item['quantity']:
                db.rollback()
                return jsonify({'success': False, 'error': f'Not enough stock for {product["name"]}'}), 400
            
            cursor.execute(
                'INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                (sale_id, item['id'], item['quantity'], item['price'])
            )
            cursor.execute(
                'UPDATE products SET stock = stock - ? WHERE id = ?',
                (item['quantity'], item['id'])
            )
        
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
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bills', methods=['GET'])
def get_bills():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    date_filter = request.args.get('filter', 'all')

    query = "SELECT * FROM sales"
    count_query = "SELECT COUNT(*) FROM sales"
    conditions = []
    params = []

    if search:
        conditions.append("id = ?")
        params.append(search)

    if date_filter != 'all':
        now = datetime.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        conditions.append("date >= ?")
        params.append(start_date.isoformat())

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions)

    total_count = db.execute(count_query, params).fetchone()[0]

    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    bills = db.execute(query, params).fetchall()

    return jsonify({
        'bills': [dict(bill) for bill in bills],
        'total_pages': (total_count + per_page - 1) // per_page,
        'total_count': total_count
    })

@app.route('/api/bills/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    db = get_db()
    sale = db.execute('SELECT * FROM sales WHERE id = ?', [bill_id]).fetchone()
    if not sale:
        return jsonify({'error': 'Bill not found'}), 404

    items = db.execute('''
        SELECT si.*, p.name 
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    ''', [bill_id]).fetchall()

    return jsonify({
        'id': sale['id'],
        'date': sale['date'],
        'subtotal': sale['subtotal'],
        'tax': sale['tax'],
        'total_amount': sale['total_amount'],
        'payment_mode': sale['payment_mode'],
        'items': [dict(item) for item in items]
    })

@app.route('/api/bills/<int:bill_id>', methods=['PUT'])
def update_bill(bill_id):
    data = request.get_json()
    
    if not data or 'items' not in data or 'edit_reason' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    
    try:
        db.execute("BEGIN TRANSACTION")

        original_items = db.execute('''
            SELECT product_id, quantity FROM sale_items 
            WHERE sale_id = ?
        ''', [bill_id]).fetchall()
        original_items_dict = {item['product_id']: item['quantity'] for item in original_items}

        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.05
        total = subtotal + tax

        db.execute('''
            UPDATE sales 
            SET subtotal = ?, tax = ?, total_amount = ?
            WHERE id = ?
        ''', [subtotal, tax, total, bill_id])

        db.execute('DELETE FROM sale_items WHERE sale_id = ?', [bill_id])

        for item in data['items']:
            db.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', [bill_id, item['product_id'], item['quantity'], item['price']])

            original_qty = original_items_dict.get(item['product_id'], 0)
            stock_diff = original_qty - item['quantity']

            if stock_diff != 0:
                db.execute('''
                    UPDATE products 
                    SET stock = stock + ?
                    WHERE id = ?
                ''', [stock_diff, item['product_id']])

        db.execute('''
            INSERT INTO bill_edits (sale_id, edit_reason, edited_at)
            VALUES (?, ?, ?)
        ''', [bill_id, data['edit_reason'], datetime.now().isoformat()])

        db.commit()
        return jsonify({'success': True})

    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def product_operations(product_id):
    db = get_db()
    if request.method == 'PUT':
        data = request.get_json()
        try:
            db.execute('''
                UPDATE products 
                SET name=?, price=?, stock=?, discount=?, barcode=?, category=?, expiry_date=?
                WHERE id=?
            ''', (
                data['name'], 
                data['price'], 
                data['stock'], 
                data.get('discount', 0),
                data.get('barcode'), 
                data.get('category'),
                data.get('expiry_date'), 
                product_id
            ))
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.execute('DELETE FROM products WHERE id=?', (product_id,))
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    db = get_db()
    
    today_sales = db.execute('''
        SELECT COALESCE(SUM(total_amount), 0) as total 
        FROM sales 
        WHERE date(date) = date('now')
    ''').fetchone()['total']
    
    total_products = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    low_stock = db.execute('SELECT COUNT(*) FROM products WHERE stock < 10').fetchone()[0]
    
    return jsonify({
        'today_sales': today_sales,
        'total_products': total_products,
        'low_stock': low_stock
    })

@app.route('/api/sales-data')
def sales_data():
    db = get_db()
    sales = db.execute('''
        SELECT date(date) as day, SUM(total_amount) as total
        FROM sales 
        WHERE date >= date('now', '-6 days')
        GROUP BY date(date)
        ORDER BY date(date)
    ''').fetchall()
    
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    sales_dict = {row['day']: row['total'] for row in sales}
    
    return jsonify({
        'labels': dates,
        'values': [sales_dict.get(date, 0) for date in dates]
    })

@app.route('/api/inventory-data')
def inventory_data():
    db = get_db()
    data = db.execute('''
        SELECT category, SUM(stock) as total 
        FROM products 
        WHERE category IS NOT NULL
        GROUP BY category
    ''').fetchall()
    
    return jsonify({
        'labels': [row['category'] for row in data],
        'values': [row['total'] for row in data]
    })

@app.route('/api/payment-data')
def payment_data():
    db = get_db()
    data = db.execute('''
        SELECT payment_mode, SUM(total_amount) as total 
        FROM sales 
        GROUP BY payment_mode
    ''').fetchall()
    
    return jsonify({
        'labels': [row['payment_mode'].capitalize() for row in data],
        'values': [row['total'] for row in data]
    })

@app.route('/api/products/low-stock')
def low_stock_products():
    db = get_db()
    products = db.execute('''
        SELECT * FROM products 
        WHERE stock < 10
        ORDER BY stock ASC
    ''').fetchall()
    return jsonify([dict(product) for product in products])

if __name__ == '__main__':
    app.run(debug=True)