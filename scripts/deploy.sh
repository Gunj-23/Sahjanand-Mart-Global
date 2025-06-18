#!/bin/bash

# Sahjanand Mart Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="sahjanand-mart"
DOCKER_IMAGE="sahjanandmart/sahjanand-mart"

echo "🚀 Deploying Sahjanand Mart to $ENVIRONMENT environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs ssl

# Set environment variables
if [ "$ENVIRONMENT" = "production" ]; then
    if [ -z "$SECRET_KEY" ]; then
        echo "⚠️  WARNING: SECRET_KEY not set. Generating random key..."
        export SECRET_KEY=$(openssl rand -hex 32)
        echo "🔑 Generated SECRET_KEY: $SECRET_KEY"
        echo "💾 Please save this key for future deployments!"
    fi
fi

# Build and deploy
echo "🔨 Building Docker image..."
docker build -t $DOCKER_IMAGE:latest .

echo "🚀 Starting services..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml up -d
else
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Performing health check..."
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "🌐 Application is available at: http://localhost"
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "🔒 Don't forget to configure SSL certificates for production!"
    fi
else
    echo "❌ Health check failed. Please check the logs:"
    docker-compose logs
    exit 1
fi

echo "📊 Service status:"
docker-compose ps

echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop services: docker-compose down"
echo "🔄 To restart services: docker-compose restart"