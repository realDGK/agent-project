# Agent System Integration Instructions

## Document Processing System Configuration

You have access to a sophisticated Agent document processing system with PostgreSQL database and LegalBERT integration.

**API Endpoint**: `http://localhost:8000` (Agent API)
**Database**: PostgreSQL with high-concurrency support
**AI Integration**: Google Gemini + LegalBERT simulation
**MCP Integration**: ✅ WORKING via Agent MCP Bridge

## Using Agent System with Goose

### Available MCP Tools
- `upload_document`: Upload and analyze documents with LegalBERT
- `query_documents`: Search and retrieve analyzed documents
- `agent_status`: Get system status including database and AI services

### Usage in Goose
Use these commands in your Goose chat:
- "Upload this document: [document content]" with filename
- "Query documents for: [search term]" or "Show recent documents"  
- "What's the agent system status?"

## Key Features

### Document Analysis Pipeline
1. **LegalBERT Integration**: Advanced legal document understanding
2. **Contract Lifecycle Tracking**: Amendment and addendum relationships
3. **Entity Extraction**: Parties, financial terms, legal terms, dates
4. **Risk Assessment**: High-value detection and complex terms analysis
5. **Human Review Workflows**: Confidence scoring and review flags

### Architecture Overview
- **Goose**: Conversational AI orchestrator (you are here)
- **Agent API**: Document processing with PostgreSQL storage
- **Web Interface**: Direct upload interface at `/web-interface.html`
- **Database**: PostgreSQL with optimized concurrency

## Example Workflows

### Document Upload
```
User: "I need to analyze this purchase agreement: [document content]"
Goose: Uses upload_document tool → Agent processes with LegalBERT → Returns analysis
```

### Document Query
```  
User: "Show me recent contract analyses"
Goose: Uses query_documents tool → Agent queries PostgreSQL → Returns formatted results
```

### System Status
```
User: "Is the document system working?"
Goose: Uses agent_status tool → Agent checks all services → Returns comprehensive status
```

## Integration Benefits

✅ **Seamless UX**: Users talk to Goose, processing happens transparently
✅ **Specialized Processing**: Agent system handles complex document analysis
✅ **Persistent Storage**: PostgreSQL database survives restarts
✅ **Scalable Architecture**: Clean separation of orchestration vs processing
✅ **Enterprise Features**: LegalBERT, lifecycle tracking, entity extraction

## System Architecture

```
User ↔ Goose (Orchestrator) ↔ MCP Bridge ↔ Agent API (PostgreSQL + LegalBERT)
```

This architecture provides the best of both worlds: conversational AI orchestration through Goose and specialized document processing through the Agent system.