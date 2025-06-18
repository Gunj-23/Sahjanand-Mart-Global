"""
Sahjanand Mart - Point of Sale System
====================================

A comprehensive POS system for retail management with inventory tracking,
billing, GST reporting, and user management.

:copyright: (c) 2024 Sahjanand Mart Team
:license: MIT License
"""

__version__ = "1.0.0"
__author__ = "Sahjanand Mart Team"
__email__ = "contact@sahjanandmart.com"

from .app import create_app

__all__ = ["create_app"]