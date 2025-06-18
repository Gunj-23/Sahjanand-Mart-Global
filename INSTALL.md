# Installation Guide for Sahjanand Mart

## Quick Installation (Recommended)

### Option 1: Automatic Setup (Windows)
```batch
# Double-click install_and_run.bat
# OR run in Command Prompt:
install_and_run.bat
```

### Option 2: Python Quick Start
```bash
python quick_start.py
```

### Option 3: Manual Installation

#### Step 1: Install the Package
```bash
# Install in development mode (recommended for local use)
pip install -e .

# OR install normally
pip install .
```

#### Step 2: Initialize Database
```bash
sahjanand-mart init-db
```

#### Step 3: Create Admin User
```bash
sahjanand-mart create-admin --username admin --password admin123
```

#### Step 4: Run the Application
```bash
sahjanand-mart run --open-browser
```

## Alternative Installation Methods

### Using pip from PyPI (when published)
```bash
pip install sahjanand-mart
sahjanand-mart init-db
sahjanand-mart create-admin
sahjanand-mart run --open-browser
```

### Using Docker
```bash
docker build -t sahjanand-mart .
docker run -d -p 8000:8000 sahjanand-mart
```

### Using Docker Compose
```bash
docker-compose up -d
# Access at http://localhost
```

## Command Line Usage

### Available Commands
```bash
sahjanand-mart --help                    # Show help
sahjanand-mart run                       # Start the application
sahjanand-mart run --debug               # Start in debug mode
sahjanand-mart run --open-browser        # Start and open browser
sahjanand-mart init-db                   # Initialize database
sahjanand-mart create-admin              # Create admin user
sahjanand-mart version                   # Show version
```

### Configuration Options
```bash
# Run on different host/port
sahjanand-mart run --host 0.0.0.0 --port 8080

# Run with custom configuration
export FLASK_ENV=production
sahjanand-mart run
```

## Troubleshooting

### Common Issues

1. **"sahjanand-mart command not found"**
   ```bash
   # Make sure you installed the package
   pip install -e .
   
   # Check if it's in your PATH
   pip show sahjanand-mart
   ```

2. **Database errors**
   ```bash
   # Reinitialize the database
   sahjanand-mart init-db
   ```

3. **Permission errors**
   ```bash
   # Run with administrator privileges (Windows)
   # OR use virtual environment
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   pip install -e .
   ```

4. **Port already in use**
   ```bash
   # Use different port
   sahjanand-mart run --port 8080
   ```

### Getting Help

- Check the logs in `logs/app.log`
- Run with `--debug` flag for more information
- Open an issue on GitHub

## Default Credentials

- **Username:** admin
- **Password:** admin123

**⚠️ Important:** Change the default password after first login!

## Next Steps

1. Login to the application
2. Add your products in the Inventory section
3. Start billing customers
4. Generate GST reports
5. Manage your business efficiently!

For more detailed documentation, see README.md