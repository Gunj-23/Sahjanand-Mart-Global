# Sahjanand Mart - Point of Sale System

A comprehensive Point of Sale (POS) system built with Flask for retail management. Features include inventory tracking, billing, GST reporting, user management, and barcode scanning.

## Features

- **Inventory Management**: Track products, stock levels, expiry dates, and categories
- **Billing System**: Create bills with barcode scanning support
- **GST Reporting**: Generate detailed GST reports and summaries
- **User Management**: Role-based access control (Admin/Employee)
- **Bill History**: View and edit previous transactions
- **Dashboard**: Real-time analytics and insights
- **Barcode Support**: Wireless barcode scanner integration
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Using pip (Recommended)

```bash
# Install the package
pip install sahjanand-mart

# Initialize the database
sahjanand-mart init-db

# Create an admin user
sahjanand-mart create-admin

# Run the application
sahjanand-mart run --open-browser
```

### Using Docker

```bash
# Clone the repository
git clone https://github.com/sahjanandmart/sahjanand-mart.git
cd sahjanand-mart

# Build and run with Docker Compose
docker-compose up -d

# Access the application at http://localhost
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sahjanandmart/sahjanand-mart.git
cd sahjanand-mart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Initialize database
sahjanand-mart init-db

# Run in development mode
sahjanand-mart run --debug --open-browser
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=production
DATABASE_PATH=./data/sahjanand_mart.db
HOST=0.0.0.0
PORT=5000
```

### Production Deployment

#### Using Gunicorn

```bash
# Install production dependencies
pip install sahjanand-mart[production]

# Run with Gunicorn
gunicorn --config gunicorn.conf.py "sahjanand_mart.app:create_app()"
```

#### Using Docker

```bash
# Build production image
docker build -t sahjanand-mart .

# Run container
docker run -d \
  --name sahjanand-mart \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  sahjanand-mart
```

#### Using Docker Compose (with Nginx)

```bash
# Set environment variables
export SECRET_KEY=your-secret-key

# Deploy with Nginx reverse proxy
docker-compose -f docker-compose.yml up -d
```

## Usage

### Command Line Interface

```bash
# Show help
sahjanand-mart --help

# Run the application
sahjanand-mart run --host 0.0.0.0 --port 5000

# Initialize database
sahjanand-mart init-db

# Create admin user
sahjanand-mart create-admin --username admin --email admin@example.com

# Show version
sahjanand-mart version
```

### Web Interface

1. **Login**: Access the system with your credentials
2. **Dashboard**: View sales analytics and inventory alerts
3. **Billing**: Create new bills with barcode scanning
4. **Inventory**: Manage products and stock levels
5. **Reports**: Generate GST reports and summaries
6. **Bill History**: View and edit previous transactions

### Barcode Scanning

The system supports wireless barcode scanners that work as keyboard input devices. Simply scan a barcode in the billing interface to add products to the cart.

## API Documentation

### Products API

```bash
# Get all products
GET /api/products

# Search products
GET /api/products?search=rice

# Get product by barcode
GET /api/products?barcode=1234567890

# Add new product
POST /api/products
Content-Type: application/json
{
  "name": "Product Name",
  "price": 10.50,
  "stock": 100,
  "barcode": "1234567890",
  "category": "Grocery"
}
```

### Sales API

```bash
# Create new sale
POST /api/sale
Content-Type: application/json
{
  "items": [
    {"id": 1, "quantity": 2, "price": 10.50}
  ],
  "total": 21.00,
  "payment_mode": "cash"
}

# Get bills
GET /api/bills?page=1&search=123

# Get bill details
GET /api/bills/123
```

## Development

### Project Structure

```
sahjanand_mart/
├── __init__.py          # Package initialization
├── app.py              # Flask application factory
├── cli.py              # Command-line interface
├── config.py           # Configuration classes
├── db.py               # Database utilities
├── schema.sql          # Database schema
├── static/             # Static files (CSS, JS, images)
├── templates/          # Jinja2 templates
tests/                  # Test suite
docs/                   # Documentation
docker/                 # Docker configuration
scripts/                # Utility scripts
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=sahjanand_mart

# Run specific test
pytest tests/test_api.py::test_products_api
```

### Code Quality

```bash
# Format code
black sahjanand_mart/

# Sort imports
isort sahjanand_mart/

# Lint code
flake8 sahjanand_mart/

# Type checking
mypy sahjanand_mart/
```

## Deployment Options

### 1. Standalone Python Application

```bash
pip install sahjanand-mart
sahjanand-mart run --host 0.0.0.0 --port 5000
```

### 2. Docker Container

```bash
docker run -d \
  --name sahjanand-mart \
  -p 8000:8000 \
  -v ./data:/app/data \
  sahjanandmart/sahjanand-mart:latest
```

### 3. Cloud Deployment

#### Heroku

```bash
# Install Heroku CLI and login
heroku create your-app-name
git push heroku main
```

#### DigitalOcean App Platform

```yaml
# .do/app.yaml
name: sahjanand-mart
services:
- name: web
  source_dir: /
  github:
    repo: your-username/sahjanand-mart
    branch: main
  run_command: gunicorn --config gunicorn.conf.py "sahjanand_mart.app:create_app()"
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
```

#### AWS EC2

```bash
# Install on Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nginx
pip3 install sahjanand-mart
sahjanand-mart init-db
sahjanand-mart create-admin

# Configure systemd service
sudo systemctl enable sahjanand-mart
sudo systemctl start sahjanand-mart
```

## Security Considerations

- Change the default `SECRET_KEY` in production
- Use HTTPS in production environments
- Regularly backup the database
- Implement proper firewall rules
- Keep dependencies updated
- Use strong passwords for admin accounts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://sahjanandmart.readthedocs.io/](https://sahjanandmart.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/sahjanandmart/sahjanand-mart/issues)
- **Email**: contact@sahjanandmart.com

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Complete POS system with inventory management
- Billing and GST reporting
- User authentication and authorization
- Barcode scanning support
- Docker deployment support