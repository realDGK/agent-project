# Agent Project - Multi-Database Contract Analysis System

## Project Overview
A sophisticated AI-powered contract analysis system with Goose orchestration and multi-database architecture for comprehensive document processing.

## Architecture Components

### 1. Databases
- **PostgreSQL 15** (Full version, not Alpine): Primary relational database with provenance tracking
- **Neo4j 5**: Graph database for document relationships and conflict resolution
- **Qdrant**: Vector database for semantic search and embeddings
- **Redis 7**: Caching and task queue management

### 2. Core Services
- **Agent Orchestrator API**: FastAPI application at `localhost:8000`
- **MCP Bridge**: Located at `config/agent_mcp_server.py` - bridges Goose to Agent API
- **Goose Integration**: Conversational AI orchestration layer

### 3. Key Features
- **Provenance Tracking**: Every extracted field carries doc_id, page, bbox, snippet, confidence
- **Conflict Engine**: Handles amendments vs originals with precedence rules
- **Table Cell Anchoring**: Cell-level tracking for financial data
- **HIL Queue**: Priority-based human review with smart batching
- **Semantic Search**: Vector similarity search via Qdrant

## Database Schema

### PostgreSQL Tables
- `documents`: Immutable document storage with SHA256 and versioning
- `extractions`: Full provenance for every extracted field
- `conflicts`: Tracks resolution of conflicting values
- `conflict_candidates`: Stores losing values with reasons
- `table_cells`: Cell-level anchoring for financial tables
- `review_tasks`: HIL queue with priority scoring
- `audit_log`: Complete audit trail

### Neo4j Relationships
- Document chains: `(:Document)-[:AMENDS]->(:Document)`
- Extraction links: `(:Document)-[:CONTAINS]->(:Extraction)`
- Conflicts: `(:Extraction)-[:CONFLICTS_WITH]->(:Extraction)`
- Encumbrances: `(:Document)-[:ENCUMBERS]->(:Parcel)`

## Deployment

### Quick Start
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and passwords

# Start multi-database stack
./deploy-multi-db.sh up dev  # Includes Adminer for DB management
# or
./deploy-multi-db.sh up prod # Production mode
```

### Management Commands
```bash
./deploy-multi-db.sh status   # Check service health
./deploy-multi-db.sh logs     # View all logs
./deploy-multi-db.sh restart  # Restart services
./deploy-multi-db.sh down     # Stop services
```

## Current State
The system has been refactored to use a containerized multi-database architecture with MCP-based communication. The previous simplified main.py successfully extracts data using Gemini AI but needs integration with the new provenance tracking system.

### Working Components
- AI extraction with Gemini 2.0 Flash/Pro
- Docker containerization for all services
- MCP bridge for Goose integration
- PostgreSQL schema with full provenance tracking
- Neo4j graph database for relationships

### In Progress
- Integration of provenance tracking into extraction pipeline
- Conflict engine implementation
- HIL queue with priority scoring
- Frontend field mapping fixes

## Development Guidelines

### Testing Commands
Run these after making changes:
```bash
# Check syntax
python -m py_compile main.py

# Run type checking if available
mypy main.py

# Test the API
curl http://localhost:8000/health
```

### Key Files
- `main.py`: Main API application (needs provenance integration)
- `simple_extraction.py`: Gemini AI extraction (working)
- `config/agent_mcp_server.py`: MCP bridge for Goose
- `docker-compose.multi-db.yml`: Multi-database configuration
- `scripts/postgres-init/01-provenance-schema.sql`: Provenance tracking schema
- `scripts/neo4j-init.cypher`: Graph database schema

## Important Notes
1. Always use full PostgreSQL, not Alpine version
2. Provenance tracking is mandatory for all extractions
3. Never skip bbox/snippet storage for audit trails
4. HIL priority = criticality * (1 - confidence) * impact
5. Conflicts must store both chosen and rejected values

## Environment Variables Required
- `GOOGLE_API_KEY`: For Gemini AI
- `POSTGRES_PASSWORD`: PostgreSQL password
- `NEO4J_PASSWORD`: Neo4j password
- Feature flags for provenance, conflicts, HIL, semantic search