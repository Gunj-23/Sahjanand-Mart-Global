#!/usr/bin/env python3
"""
Command-line interface for Sahjanand Mart POS System.
"""

import os
import sys
import click
import webbrowser
import time
from threading import Thread
from .app import create_app
from .config import config

@click.group()
@click.version_option(version='1.0.0')
def main():
    """Sahjanand Mart POS System CLI."""
    pass

@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', default='development', help='Configuration to use')
@click.option('--open-browser', is_flag=True, help='Open browser automatically')
def run(host, port, debug, config_name, open_browser):
    """Run the Sahjanand Mart application."""
    
    # Create app with specified configuration
    app = create_app(config[config_name])
    
    if open_browser:
        def open_browser_delayed():
            time.sleep(1.5)
            webbrowser.open(f'http://localhost:{port}')
        
        Thread(target=open_browser_delayed, daemon=True).start()
    
    click.echo(f"Starting Sahjanand Mart on http://{host}:{port}")
    click.echo(f"Configuration: {config_name}")
    
    if host == '0.0.0.0':
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            click.echo(f"Network access: http://{local_ip}:{port}")
        except Exception:
            pass
    
    app.run(host=host, port=port, debug=debug)

@main.command()
def init_db():
    """Initialize the database."""
    from .app import create_app
    from .db import init_db
    
    app = create_app()
    with app.app_context():
        init_db(app)
        click.echo("Database initialized successfully!")

@main.command()
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, help='Admin password')
@click.option('--email', help='Admin email')
def create_admin(username, password, email):
    """Create an admin user."""
    from .app import create_app
    from .db import get_db
    from werkzeug.security import generate_password_hash
    
    app = create_app()
    with app.app_context():
        db = get_db()
        
        # Check if user already exists
        existing_user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            click.echo(f"User '{username}' already exists!")
            return
        
        # Create admin user
        hashed_password = generate_password_hash(password)
        db.execute('''
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', (username, email, hashed_password, 'admin'))
        db.commit()
        
        click.echo(f"Admin user '{username}' created successfully!")

@main.command()
def version():
    """Show version information."""
    from . import __version__, __author__
    click.echo(f"Sahjanand Mart v{__version__}")
    click.echo(f"Author: {__author__}")

if __name__ == '__main__':
    main()