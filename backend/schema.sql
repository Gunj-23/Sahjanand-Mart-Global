-- schema.sql (updated)
-- Create products table with all columns including expiry_date and GST fields
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    discount REAL DEFAULT 0,
    barcode TEXT UNIQUE,
    category TEXT,
    expiry_date TEXT,
    cgst REAL DEFAULT 0,
    sgst REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sales table with all required columns
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtotal REAL NOT NULL,
    tax REAL NOT NULL,
    total_amount REAL NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_mode TEXT NOT NULL DEFAULT 'cash'
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'employee',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Create sale_items table
-- Update sale_items table to include GST columns
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    cgst REAL DEFAULT 0,
    sgst REAL DEFAULT 0,
    FOREIGN KEY (sale_id) REFERENCES sales (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Create bill_edits table
CREATE TABLE IF NOT EXISTS bill_edits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    edit_reason TEXT NOT NULL,
    edited_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales (id)
);

-- Sample data for products with GST values
INSERT OR IGNORE INTO products (name, price, stock, discount, barcode, category, expiry_date, cgst, sgst) VALUES
('Rice (1kg)', 45.00, 100, 0, '8901234567890', 'Grocery', '2024-12-31', 2.5, 2.5),
('Wheat Flour (1kg)', 30.00, 80, 0, '8901234567891', 'Grocery', '2024-10-31', 0, 0),
('Sugar (1kg)', 42.00, 60, 0, '8901234567892', 'Grocery', '2025-06-30', 0, 0),
('Toothpaste', 75.00, 50, 0, '8901234567893', 'Personal Care', '2025-03-31', 9, 9),
('Soap', 25.00, 120, 0, '8901234567894', 'Personal Care', '2024-09-30', 0, 0),
('Shampoo', 180.00, 40, 0, '8901234567895', 'Personal Care', '2025-01-31', 9, 9),
('Biscuits', 10.00, 200, 0, '8901234567896', 'Snacks', '2024-08-31', 0, 0),
('Chips', 20.00, 150, 0, '8901234567897', 'Snacks', '2024-07-31', 0, 0);

