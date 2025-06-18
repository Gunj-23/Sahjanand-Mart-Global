#!/bin/bash

# Sahjanand Mart Restore Script
# Usage: ./scripts/restore.sh <backup_file>

set -e

if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <backup_file>"
    echo "📋 Available backups:"
    ls -1 backups/sahjanand_mart_backup_*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite existing data!"
read -p "Are you sure you want to restore from $BACKUP_FILE? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "🔄 Stopping services..."
docker-compose down 2>/dev/null || true

echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE"

echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Restore completed successfully!"