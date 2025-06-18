from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="sahjanand-mart",
    version="1.0.0",
    author="Sahjanand Mart Team",
    author_email="contact@sahjanandmart.com",
    description="A comprehensive Point of Sale (POS) system for retail management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sahjanandmart/sahjanand-mart",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.2",
        "Werkzeug>=2.3.0",
        "Jinja2>=3.1.0",
        "click>=8.0.0",
        "itsdangerous>=2.1.0",
        "MarkupSafe>=2.1.0",
        "gunicorn>=21.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-flask>=1.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "coverage>=7.0.0",
        ],
        "windows": [
            "pywin32>=305",
        ],
    },
    entry_points={
        "console_scripts": [
            "sahjanand-mart=sahjanand_mart.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sahjanand_mart": [
            "static/**/*",
            "templates/**/*",
            "schema.sql",
        ],
    },
    zip_safe=False,
)