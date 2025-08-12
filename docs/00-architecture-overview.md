# Architecture Overview - Multi-Database Routing System

## Design Philosophy

This system implements a sophisticated multi-database architecture with intelligent query routing. Goose serves as the conversational orchestrator, while a Router Agent intelligently directs queries between two specialized backends: Cognee memory database (for conversational queries) and Agent API (for document processing). A Memory Agent monitors conversations and maintains active memory.

## Architecture Diagram

```
                    ┌─────────────────┐
                    │      User       │
                    │ (Conversation)  │
                    └─────────┬───────┘
                              │
                    ┌─────────▼───────┐
                    │     Goose       │
                    │ (Orchestrator)  │
                    └─────────┬───────┘
                              │ MCP Bridge
                    ┌─────────▼───────┐
                    │ Router Agent    │◄──── Memory Agent
                    │(Intent Analysis)│      (Background)
                    └─────┬─────┬─────┘
                          │     │
                 ┌────────▼─┐ ┌─▼──────────┐
                 │ Cognee   │ │ Agent API  │
                 │ Memory   │ │(Documents) │
                 │Database  │ │            │
                 └──────────┘ └─┬──────────┘
                                │
                      ┌─────────▼───────┐
                      │   PostgreSQL    │
                      │   (Storage)     │
                      └─────────────────┘
```

**Query Flow:**
- **Conversational** queries → Cognee Memory Database
- **Document/Business** queries → Agent API + PostgreSQL  
- **Memory Agent** monitors all conversations, stores summaries in Cognee

## Components

### 1. Goose (Conversational AI Orchestrator)
- **Purpose**: Primary user interface and conversation management
- **Technology**: Goose CLI with MCP extensions  
- **Location**: System-wide installation via `setup-environment.sh`
- **Configuration**: `config/goose/config.yaml`

**Responsibilities:**
- Handle all user conversations
- Connect to Router Agent via MCP
- Format and present results from multiple backends
- Maintain conversation context

### 2. Router Agent (`router_agent.py`)
- **Purpose**: Intelligent query routing with intent analysis
- **Technology**: Python asyncio MCP server with pattern matching
- **Location**: `config/router_agent.py`

**Capabilities:**
- `route_query`: Analyze intent and route to appropriate backend
- **Intent Types**: CONVERSATIONAL, DOCUMENT, BUSINESS, SYSTEM
- **Routing Logic**: Regex patterns for query classification
- **Backends**: Cognee Memory (port 8001) + Agent API (port 8000)

### 3. Memory Agent (`memory_agent.py`)  
- **Purpose**: Background conversation monitoring and memory extraction
- **Technology**: Python asyncio with importance scoring
- **Location**: `config/memory_agent.py`

**Capabilities:**
- Extract key decisions and document references from conversations
- Calculate importance scores (0.0 to 1.0) for memory entries
- Store structured memories in Cognee database with tags
- Maintain document pointers to Agent API database

### 4. Cognee Memory Database
- **Purpose**: Conversational memory and context storage
- **Technology**: Cognee containers with vector embeddings
- **Containers**: 
  - `cognee-dev-orchestrator` (port 8001) - Development memory
  - `cognee-business-contracts` (port 8002) - Business intelligence
- **Features**: Vector search, conversation summaries, decision tracking

### 5. Agent API (Document Processing System)
- **Purpose**: Specialized document analysis and storage
- **Technology**: FastAPI + PostgreSQL + LegalBERT simulation
- **Location**: `src/main.py`
- **Endpoints**: http://localhost:8000

**Features:**
- LegalBERT-powered document analysis
- Contract lifecycle tracking
- Entity extraction (parties, terms, dates)
- Risk assessment and compliance scoring
- PostgreSQL storage with high concurrency

### 4. PostgreSQL Database
- **Purpose**: Persistent document and analysis storage
- **Technology**: PostgreSQL 15 with optimized configuration
- **Location**: Docker container with persistent volumes

## Data Flow

### Document Upload Flow (DOCUMENT Intent)
1. **User** → Goose: "Analyze this contract: [content]"
2. **Goose** → Router Agent: `route_query` with content
3. **Router Agent** → Intent Analysis: Detects DOCUMENT intent
4. **Router Agent** → Agent API: POST `/api/analyze-document`
5. **Agent API** → LegalBERT analysis + PostgreSQL storage
6. **Agent API** → Router Agent: Structured analysis results
7. **Router Agent** → Goose: Formatted response with routing info
8. **Goose** → User: "📄 Document analyzed! Routed to Agent API..."
9. **Memory Agent** (background): Extracts key info, stores in Cognee

### Conversational Query Flow (CONVERSATIONAL Intent)
1. **User** → Goose: "What did we discuss about Acme Corp yesterday?"
2. **Goose** → Router Agent: `route_query` 
3. **Router Agent** → Intent Analysis: Detects CONVERSATIONAL intent
4. **Router Agent** → Cognee Memory DB: Search query
5. **Cognee** → Vector search through conversation memories
6. **Cognee** → Router Agent: Relevant conversation history
7. **Router Agent** → Goose: Formatted memory results
8. **Goose** → User: "📝 From our conversation history..."

### Business Query Flow (BUSINESS Intent)
1. **User** → Goose: "Find all contracts with financial terms > $100k"
2. **Goose** → Router Agent: `route_query`
3. **Router Agent** → Intent Analysis: Detects BUSINESS intent  
4. **Router Agent** → Agent API: GET `/api/documents` with filters
5. **Agent API** → PostgreSQL: Query with business logic
6. **Agent API** → Router Agent: Filtered document results
7. **Router Agent** → Goose: Formatted business results
8. **Goose** → User: "🏢 Found X high-value contracts..."

## Key Design Decisions

### Why This Multi-Database Architecture?

**✅ Intelligent Query Routing**
- Router Agent automatically detects query intent
- Routes conversational queries to memory database
- Routes document/business queries to production database
- Eliminates user confusion about which system to use

**✅ Optimized Data Stores**
- Cognee: Optimized for conversational memory and vector search
- Agent API + PostgreSQL: Optimized for document processing and business queries
- Each database handles what it does best

**✅ Background Memory Management**
- Memory Agent monitors all conversations transparently  
- Extracts key decisions and document references automatically
- Builds comprehensive memory without user intervention

**✅ Unified User Experience**
- Single interface (Goose) for all interactions
- Natural language commands work across both databases
- Users don't need to know about routing complexity

**✅ Scalability and Performance**
- Independent scaling of memory vs document processing
- Router Agent provides caching and load balancing opportunities
- Memory Agent operates asynchronously without blocking main workflow

### Alternative Architectures Considered

**❌ Direct Web Interface Only**
- Pros: Simple to understand
- Cons: No conversational interface, requires learning UI

**❌ Goose with Embedded Processing**  
- Pros: Single component
- Cons: Mixing concerns, harder to scale document processing

**❌ Multiple AI Agents**
- Pros: Distributed processing
- Cons: Complex orchestration, user confusion

## Deployment Models

### Complete Multi-Database System (Recommended)
```bash
./setup-environment.sh  # Sets up Goose + Router Agent  
docker-compose -f docker-compose.integrated.yml up -d
```
- **Full Architecture**: Goose + Router Agent + Memory Agent + Cognee + Agent API
- **Databases**: Cognee memory database + PostgreSQL document database
- **Services**: 5 containers total with intelligent routing

### Development/Testing Only  
```bash
docker-compose up -d  # Basic Agent API only
```
- **Limited Setup**: Agent API + PostgreSQL only
- **Use Case**: Direct API testing without conversational interface

### Production Considerations
- **Router Agent**: Handles load balancing between backends
- **Cognee Memory**: Can be scaled with multiple replicas
- **Agent API**: Independent scaling for document processing
- **PostgreSQL**: Use managed service for production workloads  
- **Memory Agent**: Background processing, minimal resource requirements

## Future Extensions

### Planned Features
- **Advanced Routing**: Machine learning-based intent classification
- **Multi-Agent Coordination**: Specialized agents for different document types
- **Real-time Collaboration**: Multi-user memory synchronization 
- **Workflow Automation**: Automated document processing pipelines
- **Goose UI Integration**: Upload monitoring within Goose desktop app

### Integration Points
- **Router Agent**: Easily extensible with new routing rules and backends
- **Memory Agent**: Can be enhanced with more sophisticated NLP for extraction
- **Cognee Database**: Supports additional memory types and relationships
- **Agent API**: REST endpoints allow integration with any UI or system
- **Multi-Database**: Architecture supports adding more specialized databases

## Summary

This multi-database routing architecture provides:

1. **Intelligent Query Distribution** - Automatic routing based on intent analysis
2. **Optimized Data Storage** - Right database for right query type  
3. **Transparent Memory Management** - Background conversation monitoring and extraction
4. **Unified User Experience** - Single conversational interface for complex system
5. **Independent Scalability** - Each component can be scaled based on load patterns

The system leverages the best of conversational AI (Goose), memory databases (Cognee), and specialized document processing (Agent API) while maintaining simplicity for the end user.