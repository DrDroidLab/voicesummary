#!/bin/bash

# Voice Summary Docker Deployment Script
# This script deploys the entire application with one command

set -e

echo "🚀 Starting Voice Summary deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env file from template..."
    if [ -f env.production ]; then
        cp env.production .env
        echo "✅ .env file created from env.production template"
        echo "🔧 Please edit .env file with your actual AWS credentials before continuing"
        echo "   Required variables:"
        echo "   - AWS_ACCESS_KEY_ID"
        echo "   - AWS_SECRET_ACCESS_KEY"
        echo "   - S3_BUCKET_NAME"
        echo ""
        read -p "Press Enter after you've configured the .env file..."
    else
        echo "❌ No environment template found. Please create a .env file manually."
        exit 1
    fi
fi

# Validate required environment variables
source .env
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$S3_BUCKET_NAME" ]; then
    echo "❌ Missing required environment variables in .env file:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - S3_BUCKET_NAME"
    exit 1
fi

echo "✅ Environment variables validated"

# Stop existing containers if running
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "unhealthy"; then
    echo "❌ Some services are unhealthy. Check logs with: docker-compose logs"
    exit 1
fi

echo "✅ All services are healthy!"

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec app alembic upgrade head

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 Your Voice Summary API is now running at:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "🗄️  Database management:"
echo "   - PostgreSQL: localhost:5432"
echo "   - pgAdmin: http://localhost:5050 (admin@voicesummary.com / admin123)"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - Update and redeploy: ./deploy.sh"
