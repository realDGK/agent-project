#!/bin/bash

# Cleanup script for agent project
echo "🧹 Cleaning up Agent Project..."

# Stop and remove containers
docker-compose down -v

# Remove dangling images
docker image prune -f

# Clean up logs
rm -rf logs/*

echo "✅ Cleanup complete"