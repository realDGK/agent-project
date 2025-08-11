#!/bin/bash

# Agent Project Environment Setup Script
# Configures Goose orchestrator + Agent document processing integration

set -e

echo "🔧 Setting up Agent Project Environment..."

# 1. Create Goose config directory
mkdir -p ~/.config/goose

# 2. Copy Goose configuration for Agent system integration
echo "📁 Installing Goose configuration for Agent system..."
cp -r config/goose/* ~/.config/goose/
echo "✅ Goose configuration installed (Agent MCP Bridge)"

# 3. Set up environment variables
echo "🌍 Setting up environment variables..."

# Update .bashrc with project-specific settings
if ! grep -q "# Agent Project Environment" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# Agent Project Environment
export GOOGLE_API_KEY="AIzaSyBBKeDm9XLZrwF6yYM4VWrHr6yRomBYcK4"
export PATH="$HOME/.local/bin:$PATH"

# Agent Project Aliases  
alias agent-logs="docker-compose logs -f"
alias agent-status="docker-compose ps"
alias agent-docs="curl http://localhost:8000/docs"
EOF
    echo "✅ Environment variables added to ~/.bashrc"
else
    echo "ℹ️  Agent Project environment already configured in ~/.bashrc"
fi

# 4. Load environment
source ~/.bashrc 2>/dev/null || true

# 5. Start Agent services
echo "🚀 Starting Agent services..."
docker-compose -f docker-compose.integrated.yml up -d

# 6. Wait for services to be ready
echo "⏳ Waiting for Agent API to be ready..."
sleep 15

# 7. Verify Agent system
echo "🔍 Verifying Agent system..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Agent API is running and healthy"
    
    # Test Agent system status
    echo "📊 Agent system status:"
    curl -s http://localhost:8000/api/system-status | jq '.status, .ai_service, .database' 2>/dev/null || echo "Status check complete"
    
    echo ""
    echo "✅ Goose can now orchestrate document processing through Agent system"
    echo ""
    echo "🎯 Test Goose integration with:"
    echo "   goose session start"
    echo "   > What's the agent system status?"
    echo "   > Upload this document: [paste document content here]"
    echo "   > Show recent documents"
else
    echo "⚠️  Agent API not responding. Check docker-compose status."
fi

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "📋 Architecture:"
echo "   User ↔ Goose (Orchestrator) ↔ MCP Bridge ↔ Agent API (PostgreSQL + LegalBERT)"
echo ""
echo "📋 Services available:"
echo "   • Agent API: http://localhost:8000"
echo "   • Agent Docs: http://localhost:8000/docs"
echo "   • Database: PostgreSQL on localhost:5432"
echo "   • Web Interface: ./web-interface.html"
echo ""
echo "🔧 Management commands:"
echo "   • docker-compose -f docker-compose.integrated.yml up -d - Start services"
echo "   • docker-compose -f docker-compose.integrated.yml down - Stop services"
echo "   • agent-status - Check service status"