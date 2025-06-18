import os
import sqlite3
import socket
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from .db import init_db, get_db, close_db
from .config import Config

def create_app(config_class=Config):
    """Application factory pattern for creating Flask app instances."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    
    # Register teardown handler
    @app.teardown_appcontext
    def teardown_db(exception):
        close_db()
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    # Register routes
    register_auth_routes(app)
    register_main_routes(app)
    register_api_routes(app)
    
    return app

def register_auth_routes(app):
    """Register authentication routes."""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/register', methods=['POST'])
    def register():
        username = request.form['username']
        email = request.form.get('email')
        password = request.form['password']
        role = request.form['role']
        
        db = get_db()
        try:
            existing_user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                flash('Username already exists', 'error')
                return redirect(url_for('login'))
            
            hashed_password = generate_password_hash(password)
            
            db.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed_password, role))
            db.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            db.rollback()
            flash('Registration failed: ' + str(e), 'error')
            return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out', 'success')
        return redirect(url_for('login'))

def register_main_routes(app):
    """Register main application routes."""
    
    @app.route('/')
    def dashboard():
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('dashboard.html')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/inventory')
    def inventory():
        if 'username' not in session:
            return redirect(url_for('login'))
        
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
        if 'username' not in session:
            return redirect(url_for('login'))
        
        db = get_db()
        products = db.execute('SELECT * FROM products WHERE stock > 0').fetchall()
        return render_template('billing.html', products=products)

    @app.route('/bill-history')
    def bill_history():
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('bill_history.html')

    @app.route('/gst-reports')
    def gst_reports():
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('gst_reports.html')

def register_api_routes(app):
    """Register API routes."""
    
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

    # Add all other API routes here (scan, sale, bills, etc.)
    # ... (keeping the existing API route implementations)

if __name__ == '__main__':
    app = create_app()
    
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    
    print(f"\nLocal server will be available at:")
    print(f"- This computer: http://localhost:5000")
    print(f"- Other devices: http://{local_ip}:5000")
    print("(Make sure both devices are on the same network)\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)