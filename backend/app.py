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

@app.route('/gst-reports')
def gst_reports():
    return render_template('gst_reports.html')

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
                INSERT INTO products (name, price, stock, discount, barcode, category, expiry_date, cgst, sgst)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['price'],
                data['stock'],
                data.get('discount', 0),
                data.get('barcode'),
                data.get('category'),
                data.get('expiry_date'),
                data.get('cgst', 0),
                data.get('sgst', 0)
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
        tax = 0  # Tax is now included in MRP
        
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
                'INSERT INTO sale_items (sale_id, product_id, quantity, price, cgst, sgst) VALUES (?, ?, ?, ?, ?, ?)',
                (sale_id, item['id'], item['quantity'], item['price'], product['cgst'], product['sgst'])
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

    # Base query
    query = 'SELECT * FROM sales'
    count_query = 'SELECT COUNT(*) FROM sales'
    conditions = []
    params = []

    if search:
        try:
            bill_id = int(search)
            conditions.append("id = ?")
            params.append(bill_id)
        except ValueError:
            return jsonify({
                'bills': [],
                'total_pages': 0,
                'total_count': 0
            })

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
        params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        query += where_clause
        count_query += where_clause

    # Get total count
    total_count = db.execute(count_query, params).fetchone()[0]

    # Get paginated results
    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    bills = db.execute(query, params).fetchall()

    # Convert to list of dicts
    bills_list = []
    for bill in bills:
        bill_dict = dict(bill)
        try:
            bill_date = datetime.strptime(bill_dict['date'], '%Y-%m-%d %H:%M:%S')
            bill_dict['date'] = bill_date.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass
        bills_list.append(bill_dict)

    return jsonify({
        'bills': bills_list,
        'total_pages': (total_count + per_page - 1) // per_page,
        'total_count': total_count
    })

@app.route('/api/bills/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    db = get_db()
    
    # Get sale information
    sale = db.execute('SELECT * FROM sales WHERE id = ?', [bill_id]).fetchone()
    if not sale:
        return jsonify({'error': 'Bill not found'}), 404

    # Get sale items with product names
    items = db.execute('''
        SELECT si.*, p.name 
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    ''', [bill_id]).fetchall()

    # Get edit history
    edits = db.execute('''
        SELECT * FROM bill_edits
        WHERE sale_id = ?
        ORDER BY edited_at DESC
    ''', [bill_id]).fetchall()

    # Format response
    response = {
        'id': sale['id'],
        'date': sale['date'],
        'subtotal': sale['subtotal'],
        'tax': sale['tax'],
        'total_amount': sale['total_amount'],
        'payment_mode': sale['payment_mode'],
        'items': [dict(item) for item in items],
        'edits': [dict(edit) for edit in edits]
    }

    return jsonify(response)

@app.route('/api/bills/<int:bill_id>', methods=['PUT'])
def update_bill(bill_id):
    data = request.get_json()
    
    if not data or 'items' not in data or 'edit_reason' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    
    try:
        db.execute("BEGIN TRANSACTION")

        # Get original items for stock reconciliation
        original_items = db.execute('''
            SELECT product_id, quantity FROM sale_items 
            WHERE sale_id = ?
        ''', [bill_id]).fetchall()
        original_items_dict = {item['product_id']: item['quantity'] for item in original_items}

        # Calculate new totals
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = 0  # Tax is now included in MRP
        total = subtotal + tax

        # Update sale record
        db.execute('''
            UPDATE sales 
            SET subtotal = ?, tax = ?, total_amount = ?
            WHERE id = ?
        ''', [subtotal, tax, total, bill_id])

        # Delete existing sale items
        db.execute('DELETE FROM sale_items WHERE sale_id = ?', [bill_id])

        # Insert new sale items and update stock
        for item in data['items']:
            db.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, price, cgst, sgst)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [bill_id, item['product_id'], item['quantity'], item['price'], item.get('cgst', 0), item.get('sgst', 0)])

            # Calculate stock difference and update products
            original_qty = original_items_dict.get(item['product_id'], 0)
            stock_diff = original_qty - item['quantity']

            if stock_diff != 0:
                db.execute('''
                    UPDATE products 
                    SET stock = stock + ?
                    WHERE id = ?
                ''', [stock_diff, item['product_id']])

        # Record the edit
        db.execute('''
            INSERT INTO bill_edits (sale_id, edit_reason, edited_at)
            VALUES (?, ?, ?)
        ''', [bill_id, data['edit_reason'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

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
                SET name=?, price=?, stock=?, discount=?, barcode=?, category=?, expiry_date=?, cgst=?, sgst=?
                WHERE id=?
            ''', (
                data['name'], 
                data['price'], 
                data['stock'], 
                data.get('discount', 0),
                data.get('barcode'), 
                data.get('category'),
                data.get('expiry_date'), 
                data.get('cgst', 0),
                data.get('sgst', 0),
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

@app.route('/api/products/expiring-soon')
def expiring_soon_products():
    db = get_db()
    products = db.execute('''
        SELECT * FROM products 
        WHERE expiry_date IS NOT NULL 
        AND expiry_date BETWEEN date('now') AND date('now', '+30 days')
        ORDER BY expiry_date ASC
    ''').fetchall()
    return jsonify([dict(product) for product in products])

@app.route('/api/products/expired')
def expired_products():
    db = get_db()
    products = db.execute('''
        SELECT * FROM products 
        WHERE expiry_date IS NOT NULL 
        AND expiry_date < date('now')
        ORDER BY expiry_date ASC
    ''').fetchall()
    return jsonify([dict(product) for product in products])

@app.route('/api/products/add-lot', methods=['POST'])
def add_product_lot():
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    db = get_db()
    try:
        # Get current product
        product = db.execute('SELECT * FROM products WHERE id = ?', [data['product_id']]).fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        # Update stock
        new_stock = product['stock'] + data['quantity']
        
        # Update expiry date if provided and it's earlier than current expiry
        update_expiry = ''
        expiry_params = []
        if data.get('expiry_date'):
            if not product['expiry_date'] or data['expiry_date'] < product['expiry_date']:
                update_expiry = ', expiry_date = ?'
                expiry_params = [data['expiry_date']]

        query = f'UPDATE products SET stock = ?{update_expiry} WHERE id = ?'
        params = [new_stock] + expiry_params + [data['product_id']]
        
        db.execute(query, params)
        db.commit()
        
        return jsonify({
            'success': True,
            'new_stock': new_stock
        })
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/gst-reports', methods=['GET'])
def get_gst_reports():
    db = get_db()
    period = request.args.get('period', 'today')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Define date ranges based on period
    if period == 'today':
        date_condition = "date(date) = date('now')"
    elif period == 'week':
        date_condition = "date(date) >= date('now', 'weekday 0', '-7 days')"
    elif period == 'month':
        date_condition = "strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
    elif period == 'quarter':
        date_condition = "strftime('%Y-%m', date) IN (strftime('%Y-%m', 'now'), strftime('%Y-%m', 'now', '-1 month'), strftime('%Y-%m', 'now', '-2 months'))"
    elif period == 'year':
        date_condition = "strftime('%Y', date) = strftime('%Y', 'now')"
    elif period == 'custom' and start_date and end_date:
        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            date_condition = f"date(date) BETWEEN date('{start_date}') AND date('{end_date}')"
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        date_condition = "1=1"  # All time
    
    # Get inventory stats (not date dependent)
    inventory_stats = db.execute('''
        SELECT 
            SUM(CASE WHEN cgst > 0 OR sgst > 0 THEN stock ELSE 0 END) as gst_products_count,
            SUM(CASE WHEN cgst = 0 AND sgst = 0 THEN stock ELSE 0 END) as non_gst_products_count,
            SUM(CASE WHEN cgst > 0 OR sgst > 0 THEN stock * price ELSE 0 END) as gst_products_value,
            SUM(CASE WHEN cgst = 0 AND sgst = 0 THEN stock * price ELSE 0 END) as non_gst_products_value,
            SUM(CASE WHEN cgst > 0 OR sgst > 0 THEN stock * price * (cgst + sgst) / 100 ELSE 0 END) as gst_tax_value,
            SUM(CASE WHEN cgst > 0 OR sgst > 0 THEN stock * price * cgst / 100 ELSE 0 END) as cgst_value,
            SUM(CASE WHEN cgst > 0 OR sgst > 0 THEN stock * price * sgst / 100 ELSE 0 END) as sgst_value
        FROM products
    ''').fetchone()
    
    # Get sales stats (date dependent)
    sales_stats = db.execute(f'''
        SELECT 
            SUM(CASE WHEN p.cgst > 0 OR p.sgst > 0 THEN si.quantity ELSE 0 END) as gst_products_sold,
            SUM(CASE WHEN p.cgst = 0 AND p.sgst = 0 THEN si.quantity ELSE 0 END) as non_gst_products_sold,
            SUM(CASE WHEN p.cgst > 0 OR p.sgst > 0 THEN si.quantity * si.price ELSE 0 END) as gst_products_sales,
            SUM(CASE WHEN p.cgst = 0 AND p.sgst = 0 THEN si.quantity * si.price ELSE 0 END) as non_gst_products_sales,
            SUM(CASE WHEN p.cgst > 0 OR p.sgst > 0 THEN si.quantity * si.price * (p.cgst + p.sgst) / 100 ELSE 0 END) as gst_tax_collected,
            SUM(CASE WHEN p.cgst > 0 OR p.sgst > 0 THEN si.quantity * si.price * p.cgst / 100 ELSE 0 END) as cgst_collected,
            SUM(CASE WHEN p.cgst > 0 OR p.sgst > 0 THEN si.quantity * si.price * p.sgst / 100 ELSE 0 END) as sgst_collected
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE {date_condition}
    ''').fetchone()
    
    return jsonify({
        'inventory': {
            'gst_products_count': inventory_stats['gst_products_count'] or 0,
            'non_gst_products_count': inventory_stats['non_gst_products_count'] or 0,
            'gst_products_value': inventory_stats['gst_products_value'] or 0,
            'non_gst_products_value': inventory_stats['non_gst_products_value'] or 0,
            'gst_tax_value': inventory_stats['gst_tax_value'] or 0,
            'cgst_value': inventory_stats['cgst_value'] or 0,
            'sgst_value': inventory_stats['sgst_value'] or 0
        },
        'sales': {
            'gst_products_sold': sales_stats['gst_products_sold'] or 0,
            'non_gst_products_sold': sales_stats['non_gst_products_sold'] or 0,
            'gst_products_sales': sales_stats['gst_products_sales'] or 0,
            'non_gst_products_sales': sales_stats['non_gst_products_sales'] or 0,
            'gst_tax_collected': sales_stats['gst_tax_collected'] or 0,
            'cgst_collected': sales_stats['cgst_collected'] or 0,
            'sgst_collected': sales_stats['sgst_collected'] or 0
        },
        'period': period,
        'start_date': start_date if period == 'custom' else None,
        'end_date': end_date if period == 'custom' else None
    })

@app.route('/api/gst-reports/detailed', methods=['GET'])
def get_detailed_gst_report():
    db = get_db()
    period = request.args.get('period', 'today')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Define date ranges based on period
    if period == 'today':
        date_condition = "date(s.date) = date('now')"
    elif period == 'week':
        date_condition = "date(s.date) >= date('now', 'weekday 0', '-7 days')"
    elif period == 'month':
        date_condition = "strftime('%Y-%m', s.date) = strftime('%Y-%m', 'now')"
    elif period == 'quarter':
        date_condition = "strftime('%Y-%m', s.date) IN (strftime('%Y-%m', 'now'), strftime('%Y-%m', 'now', '-1 month'), strftime('%Y-%m', 'now', '-2 months'))"
    elif period == 'year':
        date_condition = "strftime('%Y', s.date) = strftime('%Y', 'now')"
    elif period == 'custom' and start_date and end_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            date_condition = f"date(s.date) BETWEEN date('{start_date}') AND date('{end_date}')"
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        date_condition = "1=1"  # All time
    
    # Get detailed GST report data
    detailed_data = db.execute(f'''
        SELECT 
            p.name,
            p.cgst,
            p.sgst,
            SUM(si.quantity) as quantity,
            si.price
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE {date_condition}
        AND (p.cgst > 0 OR p.sgst > 0)
        GROUP BY p.id, si.price
        ORDER BY p.name
    ''').fetchall()
    
    return jsonify([dict(row) for row in detailed_data])

@app.route('/api/gst-reports/print', methods=['POST'])
def print_gst_report():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    try:
        # Return success as we're handling printing client-side now
        return jsonify({
            'success': True,
            'message': 'Printing handled client-side',
            'data': data  # Return the data back for client-side use
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)