# Cognee Memory Integration Instructions

## Memory System Configuration

You have access to a containerized Cognee memory system that stores project knowledge and architectural decisions.

**Container**: `cognee-dev-orchestrator` (development memory)
**Database**: SQLite with persistent Docker volumes at `/app/data/cognee_system/databases/`
**Embedding Model**: `gemini-embedding-001` (Google AI Studio free tier)
**MCP Integration**: ✅ WORKING via containerized MCP server

## Using Cognee with Goose

### Available MCP Tools
- `cognee_store`: Store knowledge in the database
- `cognee_search`: Search stored knowledge  
- `cognee_status`: Get database status

### Usage in Goose
Use these commands in your Goose chat:
- "Store this in cognee: [your information]"
- "Search cognee for: [your query]"
- "What's the cognee status?"

## Key Project Context Already Stored

1. **Architecture**: Hybrid system with Goose as orchestrator and dual Cognee instances
2. **Docker Cleanup**: Successfully consolidated 6+ duplicate docker-compose files
3. **Database Strategy**: Separate databases for dev/orchestrator vs business intelligence
4. **Embedding Model**: Using gemini-embedding-001 for cost efficiency
5. **Containerization**: Complete with persistent volumes for data retention

## MCP Configuration

The system uses MCP (Model Context Protocol) for direct integration with Goose:
- Server script: `/tmp/cognee_mcp.py` (containerized)
- Transport: stdio via Docker exec
- Status: ✅ Tested and working

## Container Management

- Start services: `docker-compose up -d`
- Check status: `docker-compose ps`
- View logs: `docker logs cognee-dev-orchestrator`
- Shell access: `docker exec -it cognee-dev-orchestrator /bin/bash`

## Data Persistence

All knowledge is stored in Docker volumes:
- `cognee_dev_data`: Application data
- `cognee_dev_database`: SQLite database files
- `cognee_dev_cache`: Cache data
- `cognee_dev_logs`: Application logs

This ensures knowledge survives container restarts and system reboots.