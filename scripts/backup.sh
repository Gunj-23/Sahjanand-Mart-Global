#!/bin/bash

# Sahjanand Mart Backup Script
# Usage: ./scripts/backup.sh

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="sahjanand_mart_backup_$TIMESTAMP.tar.gz"

echo "💾 Creating backup of Sahjanand Mart..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
echo "📦 Creating backup archive..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='logs/*.log' \
    data/ \
    .env 2>/dev/null || true

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE"

# Keep only last 10 backups
echo "🧹 Cleaning old backups..."
cd $BACKUP_DIR
ls -t sahjanand_mart_backup_*.tar.gz | tail -n +11 | xargs -r rm --

echo "📊 Available backups:"
ls -lh sahjanand_mart_backup_*.tar.gz 2>/dev/null || echo "No backups found"

echo "✅ Backup completed successfully!"