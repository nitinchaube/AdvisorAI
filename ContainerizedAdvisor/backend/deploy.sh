#!/bin/bash

# AdvisorAI Backend Deployment Script for EC2
# This script deploys both Redis and Backend on a single EC2 instance

set -e

echo "🚀 Starting AdvisorAI Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads VectorDB Data

# Set proper permissions
print_status "Setting permissions..."
chmod -R 755 uploads VectorDB Data

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f ".env.prod" ]; then
        cp .env.prod .env
        print_status "Created .env from .env.prod template"
        print_warning "Please update .env with your actual environment variables"
    else
        print_error ".env.prod template not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if Firebase credentials exist
if [ ! -f "firebae_key1.json" ]; then
    print_error "Firebase credentials file (firebae_key1.json) not found!"
    print_warning "Please ensure you have the Firebase service account key file."
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Remove old images (optional)
print_status "Cleaning up old images..."
docker image prune -f || true

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Test Redis connection
print_status "Testing Redis connection..."
if docker exec advisorai_redis redis-cli ping | grep -q "PONG"; then
    print_status "✅ Redis is running and responding"
else
    print_error "❌ Redis is not responding"
fi

# Test Backend health
print_status "Testing Backend health..."
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    print_status "✅ Backend is running and healthy"
else
    print_warning "⚠️  Backend health check failed, but service might still be starting"
fi

# Show logs
print_status "Showing recent logs..."
docker-compose -f docker-compose.prod.yml logs --tail=20

print_status "🎉 Deployment completed!"
print_status "Backend is available at: http://localhost:5000"
print_status "Redis is available at: localhost:6379"
print_status ""
print_status "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
print_status "To stop services: docker-compose -f docker-compose.prod.yml down"
print_status "To restart services: docker-compose -f docker-compose.prod.yml restart"
