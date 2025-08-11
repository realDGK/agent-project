# Architecture Overview - Goose + Agent Integration

## Design Philosophy

This system implements a clean separation between conversational AI orchestration (Goose) and specialized document processing (Agent API). Users interact only with Goose, which transparently handles complex document analysis through the Agent system.

## Architecture Diagram

```
┌─────────────────┐    MCP Bridge    ┌─────────────────┐
│                 │◄─────────────────►│                 │
│     Goose       │                  │   Agent API     │
│  (Orchestrator) │                  │ (Processor)     │
│                 │                  │                 │
└─────────────────┘                  └─────────────────┘
         ▲                                     │
         │                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│                 │                  │                 │
│      User       │                  │   PostgreSQL    │
│ (Conversation)  │                  │   (Storage)     │
│                 │                  │                 │
└─────────────────┘                  └─────────────────┘
```

## Components

### 1. Goose (Conversational AI Orchestrator)
- **Purpose**: Primary user interface and conversation management
- **Technology**: Goose CLI with MCP extensions  
- **Location**: System-wide installation via `setup-environment.sh`
- **Configuration**: `config/goose/config.yaml`

**Responsibilities:**
- Handle all user conversations
- Orchestrate document processing requests
- Format and present results
- Maintain conversation context

### 2. MCP Bridge (`agent_mcp_server.py`)
- **Purpose**: Protocol translation between Goose and Agent API
- **Technology**: Python asyncio MCP server
- **Location**: `config/agent_mcp_server.py`

**Capabilities:**
- `upload_document`: Send documents to Agent API for analysis
- `query_documents`: Retrieve processed documents from database  
- `agent_status`: Monitor Agent system health

### 3. Agent API (Document Processing System)
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

### Document Upload Flow
1. **User** → Goose: "Analyze this contract: [content]"
2. **Goose** → MCP Bridge: `upload_document` call
3. **MCP Bridge** → Agent API: POST `/api/analyze-document`
4. **Agent API** → LegalBERT analysis + PostgreSQL storage
5. **Agent API** → MCP Bridge: Structured analysis results
6. **MCP Bridge** → Goose: Formatted response
7. **Goose** → User: "Document analyzed! Here are the results..."

### Document Query Flow  
1. **User** → Goose: "Show recent contract analyses"
2. **Goose** → MCP Bridge: `query_documents` call
3. **MCP Bridge** → Agent API: GET `/api/documents`
4. **Agent API** → PostgreSQL: Query recent documents
5. **Agent API** → MCP Bridge: Document list with metadata
6. **MCP Bridge** → Goose: Formatted document list
7. **Goose** → User: "Found X documents: [list]"

## Key Design Decisions

### Why This Architecture?

**✅ Clean Separation of Concerns**
- Goose: Excellent at conversation and orchestration
- Agent API: Specialized for document processing
- Each component does what it does best

**✅ User Experience**
- Single interface (Goose) for all interactions
- Natural language commands
- No need to learn API endpoints or web interfaces

**✅ Scalability**
- Agent API can be scaled independently
- PostgreSQL handles high concurrency
- MCP bridge is stateless and lightweight

**✅ Development Efficiency**
- Leverage existing Goose ecosystem
- Reuse our sophisticated Agent document processing
- Clear integration boundaries

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

### Development
```bash
./setup-environment.sh
```
- Single command setup
- Goose + Agent API + PostgreSQL
- Ideal for development and testing

### Production Considerations
- Agent API can be deployed separately/scaled
- PostgreSQL can use managed service
- MCP bridge runs locally with Goose
- Multiple Agent API instances behind load balancer

## Future Extensions

### Planned Features
- **Goose UI Integration**: Upload monitoring within Goose desktop app
- **Semantic Search**: Vector similarity search via Agent API
- **Workflow Automation**: Multi-step document processing chains
- **Real-time Notifications**: Document processing status updates

### Integration Points
- All extensions connect through the MCP bridge
- Agent API provides REST endpoints for any UI
- PostgreSQL schema supports additional metadata
- Clean architecture supports easy feature addition

This architecture provides the foundation for a scalable, user-friendly contract analysis system that leverages the best of both conversational AI and specialized document processing.