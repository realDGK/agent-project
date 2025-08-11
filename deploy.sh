#!/bin/bash

# Agent Project Deployment Script
set -e

echo "🚀 Agent Project Deployment Starting..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found. Please copy .env.example to .env and configure."
    exit 1
fi

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "GOOGLE_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment validation complete"

# Create volumes if they don't exist
mkdir -p volumes/postgres_data
mkdir -p volumes/cognee_data
mkdir -p logs

echo "✅ Volume directories created"

# Build and start services
echo "📦 Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to become healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ API Backend is healthy"
else
    echo "⚠️  API Backend health check failed"
    docker-compose logs agent-orchestrator
fi

# Display service URLs
echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Service URLs:"
echo "   API Backend: http://localhost:8000"
echo "   Health Check: http://localhost:8000/health"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "📝 View logs with: docker-compose logs -f [service-name]"
echo "🛑 Stop services with: docker-compose down"