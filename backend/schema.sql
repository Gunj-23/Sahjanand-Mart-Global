-- Create products table with all columns including expiry_date
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    barcode TEXT UNIQUE,
    category TEXT,
    expiry_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create sales table with all required columns
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    subtotal NUMERIC NOT NULL,
    tax NUMERIC NOT NULL,
    total_amount NUMERIC NOT NULL,
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payment_mode TEXT NOT NULL DEFAULT 'cash'
);

-- Create sale_items table
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    price NUMERIC NOT NULL
);

-- Sample data for products
INSERT INTO products (name, price, stock, barcode, category, expiry_date) VALUES
('Rice (1kg)', 45.00, 100, '8901234567890', 'Grocery', '2024-12-31'),
('Wheat Flour (1kg)', 30.00, 80, '8901234567891', 'Grocery', '2024-10-31'),
('Sugar (1kg)', 42.00, 60, '8901234567892', 'Grocery', '2025-06-30'),
('Toothpaste', 75.00, 50, '8901234567893', 'Personal Care', '2025-03-31'),
('Soap', 25.00, 120, '8901234567894', 'Personal Care', '2024-09-30'),
('Shampoo', 180.00, 40, '8901234567895', 'Personal Care', '2025-01-31'),
('Biscuits', 10.00, 200, '8901234567896', 'Snacks', '2024-08-31'),
('Chips', 20.00, 150, '8901234567897', 'Snacks', '2024-07-31')
ON CONFLICT (barcode) DO NOTHING;
