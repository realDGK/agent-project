#!/bin/bash

# Multi-Database Deployment Script
# Sets up PostgreSQL, Neo4j, Qdrant, and Redis for Agent System

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================>${NC}"
echo -e "${GREEN}     Agent Multi-Database Deployment Script    ${NC}"
echo -e "${GREEN}==============================================>${NC}"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration:${NC}"
        echo -e "${YELLOW}  - Set GOOGLE_API_KEY${NC}"
        echo -e "${YELLOW}  - Set secure passwords for POSTGRES_PASSWORD and NEO4J_PASSWORD${NC}"
        echo -e "${RED}Exiting. Please configure .env and run again.${NC}"
        exit 1
    else
        echo -e "${RED}No .env.example file found!${NC}"
        exit 1
    fi
fi

# Source environment variables
source .env

# Validate required environment variables
if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" == "secure_postgres_password_here" ]; then
    echo -e "${RED}Error: POSTGRES_PASSWORD not configured in .env${NC}"
    exit 1
fi

if [ -z "$NEO4J_PASSWORD" ] || [ "$NEO4J_PASSWORD" == "secure_neo4j_password_here" ]; then
    echo -e "${RED}Error: NEO4J_PASSWORD not configured in .env${NC}"
    exit 1
fi

# Function to check if a service is healthy
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.multi-db.yml ps | grep -q "$service.*healthy"; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}✗ $service failed to become healthy${NC}"
    return 1
}

# Parse command line arguments
ACTION=${1:-up}
PROFILE=${2:-prod}

case $ACTION in
    up|start)
        echo -e "${GREEN}Starting multi-database stack...${NC}"
        
        # Create necessary directories
        echo -e "${YELLOW}Creating volume directories...${NC}"
        mkdir -p volumes/{postgres_data,neo4j_data,neo4j_logs,neo4j_import,neo4j_plugins,qdrant_storage,qdrant_snapshots,redis_data}
        
        # Set permissions for Neo4j directories
        chmod 777 volumes/neo4j_*
        
        # Start services
        if [ "$PROFILE" == "dev" ]; then
            echo -e "${YELLOW}Starting services with dev profile (includes Adminer)...${NC}"
            docker-compose -f docker-compose.multi-db.yml --profile dev up -d
        else
            echo -e "${YELLOW}Starting production services...${NC}"
            docker-compose -f docker-compose.multi-db.yml up -d
        fi
        
        # Wait for services to be healthy
        echo ""
        check_service_health "agent-postgres"
        check_service_health "agent-neo4j"
        check_service_health "agent-qdrant"
        check_service_health "agent-redis"
        
        # Initialize Neo4j with schema
        echo -e "${YELLOW}Initializing Neo4j schema...${NC}"
        sleep 10  # Extra wait for Neo4j to be fully ready
        
        if [ -f scripts/neo4j-init.cypher ]; then
            docker exec -i agent-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" < scripts/neo4j-init.cypher 2>/dev/null || true
            echo -e "${GREEN}✓ Neo4j schema initialized${NC}"
        fi
        
        # Check agent-orchestrator health
        echo -e "${YELLOW}Waiting for Agent Orchestrator...${NC}"
        check_service_health "agent-orchestrator"
        
        echo ""
        echo -e "${GREEN}==============================================>${NC}"
        echo -e "${GREEN}Multi-database stack is running!${NC}"
        echo ""
        echo -e "${GREEN}Services available at:${NC}"
        echo -e "  • Agent API:        http://localhost:8000"
        echo -e "  • PostgreSQL:       localhost:5432"
        echo -e "  • Neo4j Browser:    http://localhost:7474"
        echo -e "  • Neo4j Bolt:       bolt://localhost:7687"
        echo -e "  • Qdrant Dashboard: http://localhost:6333/dashboard"
        echo -e "  • Redis:            localhost:6379"
        if [ "$PROFILE" == "dev" ]; then
            echo -e "  • Adminer:          http://localhost:8080"
        fi
        echo ""
        echo -e "${GREEN}Database credentials:${NC}"
        echo -e "  • PostgreSQL: agent_user / [your password]"
        echo -e "  • Neo4j:      neo4j / [your password]"
        echo -e "${GREEN}==============================================>${NC}"
        ;;
        
    down|stop)
        echo -e "${YELLOW}Stopping multi-database stack...${NC}"
        docker-compose -f docker-compose.multi-db.yml down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting multi-database stack...${NC}"
        $0 down
        sleep 2
        $0 up $PROFILE
        ;;
        
    logs)
        SERVICE=${2:-}
        if [ -z "$SERVICE" ]; then
            docker-compose -f docker-compose.multi-db.yml logs -f
        else
            docker-compose -f docker-compose.multi-db.yml logs -f $SERVICE
        fi
        ;;
        
    status)
        echo -e "${GREEN}Service Status:${NC}"
        docker-compose -f docker-compose.multi-db.yml ps
        ;;
        
    clean)
        echo -e "${RED}WARNING: This will delete all data!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            docker-compose -f docker-compose.multi-db.yml down -v
            rm -rf volumes/*
            echo -e "${GREEN}✓ All data cleaned${NC}"
        else
            echo "Cancelled"
        fi
        ;;
        
    *)
        echo "Usage: $0 {up|down|restart|logs|status|clean} [dev|prod]"
        echo ""
        echo "Commands:"
        echo "  up [dev|prod]  - Start services (dev includes Adminer)"
        echo "  down           - Stop services"
        echo "  restart        - Restart services"
        echo "  logs [service] - View logs (optional: specific service)"
        echo "  status         - Show service status"
        echo "  clean          - Remove all containers and data"
        exit 1
        ;;
esac