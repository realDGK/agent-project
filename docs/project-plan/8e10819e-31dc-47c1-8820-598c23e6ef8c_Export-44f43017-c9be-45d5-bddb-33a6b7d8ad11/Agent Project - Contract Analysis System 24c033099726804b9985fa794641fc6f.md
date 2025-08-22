# Agent Project - Contract Analysis System

A sophisticated AI-powered contract analysis system with Goose orchestration and PostgreSQL-based document processing.

**## Architecture**

```

User ↔ Goose (Conversational AI Orchestrator)

↓ (MCP Bridge)

Agent API (PostgreSQL + LegalBERT Document Processing)

```

- ***Key Design Principles:****
- ***Goose****: Handles all user conversations and orchestration
- ***Agent System****: Specialized document processing with LegalBERT
- ***Clean Separation****: Conversational AI vs. Document Processing
- ***Unified Experience****: Users only interact with Goose

**## Quick Start**

**### Recommended: Full Goose Integration**

1. ****Complete Environment Setup****

```bash

./setup-environment.sh

```

2. ****Test Integration****

```bash

goose session start

> What's the agent system status?

> Upload this document: [paste content]

> Show recent documents

```

**### Alternative: Agent API Only**

1. ****Launch Agent Services****

```bash

./deploy.sh

```

2. ****Access Services****

- API Backend: http://localhost:8000/docs

- Web Interface: ./web-interface.html

**## Project Structure**

```

agent-project/

├── .env                            # Environment configuration

├── docker-compose.yml             # Basic Agent services

├── docker-compose.integrated.yml  # Complete Goose + Agent integration

├── setup-environment.sh           # One-command full setup

├── src/                           # Agent application source code

│   ├── app/                      # Backend API with LegalBERT

│   └── main.py                   # FastAPI application entry point

├── config/                       # Configuration files

│   ├── goose/                   # Goose CLI configuration

│   ├── agent_mcp_server.py     # MCP bridge: Goose ↔ Agent API

│   └── agent-instructions.md   # Usage guide for integration

├── docs/                         # Documentation

├── scripts/                      # Deployment and utility scripts

└── volumes/                      # Persistent PostgreSQL data

```

**## Features**

**### Goose Integration**

- 💬 ***Conversational Interface**** - Natural language document processing
- 🔄 ***MCP Bridge**** - Seamless connection between Goose and Agent API
- 📝 ***Session Management**** - Persistent conversation history
- 🎯 ***Command Orchestration**** - Upload, query, and manage documents via chat

**### Document Processing**

- 🤖 ***LegalBERT Analysis**** - Specialized legal document understanding
- 📋 ***Contract Lifecycle**** - Amendment and addendum relationship tracking
- 🏷️ ***Entity Extraction**** - Parties, financial terms, dates, legal clauses
- ⚖️ ***Risk Assessment**** - Automated compliance and complexity scoring
- 🔍 ***Semantic Search**** - PostgreSQL-based document retrieval

**### Infrastructure**

- 🗄️ ***PostgreSQL Backend**** - High-concurrency database with connection pooling
- 🔄 ***Agent API**** - RESTful document processing endpoints
- 🌐 ***Web Interface**** - Direct upload alternative to Goose
- 🔒 ***Enterprise Security**** - Secure API design with audit trails

**## UI Integration Design**

**### Future: Goose Desktop App Enhancement**

The next phase will integrate document upload functionality directly into the Goose desktop UI:

```
```
┌─────────────────────────────────────┐
│ Goose Desktop UI                    │
│ ┌─────────────────┐ ┌─────────────┐ │
│ │   Chat Panel    │ │ Upload Panel│ │
│ │                 │ │             │ │  
│ │ User: Upload    │ │ [Drop Zone] │ │
│ │ this contract   │ │             │ │
│ │                 │ │ ┌─────────┐ │ │
│ │ Agent: Analysis │ │ │ Monitor │ │ │◄─── Agent API
│ │ complete!       │ │ │ Status  │ │ │     (Background)
│ │                 │ │ └─────────┘ │ │
│ └─────────────────┘ └─────────────┘ │
└─────────────────────────────────────┘
```
```

- ***Key Design Principles:****
- ***Goose UI****: Handles upload interface and user interaction
- ***Agent System****: Monitors and processes uploads in background
- ***Unified Experience****: All document work happens within Goose interface

**## Documentation**

- [Architecture Overview](docs/00-architecture-overview.md) - ***START HERE****
- [System Overview](docs/01-system-overview.md)
- [Current Implementation](docs/02-current-implementation.md)
- [Technical Roadmap](docs/03-technical-roadmap.md)
- [Deployment Guide](docs/04-deployment-guide.md)
- [Next Phase Priorities](docs/05-next-phase-priorities.md)

**## Development**

Built with:

- ***Backend****: FastAPI, PostgreSQL, Redis
- ***AI/ML****: Google Gemini, LegalBERT integration
- ***Infrastructure****: Docker, Docker Compose
- ***Frontend****: Modern web technologies with drag-and-drop interface

**## License**

Proprietary - All rights reserved

[**Architecture Overview - Goose + Agent Integration**](Architecture%20Overview%20-%20Goose%20+%20Agent%20Integration%2024c033099726803f8bf0db626eecadde.md)

[**Documentation Migration & Consolidation**](Documentation%20Migration%20&%20Consolidation%2024c03309972680f19ef7f7ff349b9f6f.md)

[](Untitled%2024c0330997268033a122f6dfbfaaa756.md)

[Graphic Interface file reference ](Graphic%20Interface%20file%20reference%2024d0330997268092b23bcaeaa395f234.md)

[Business Rules](Business%20Rules%2025003309972680ecb7cac5f593603d01.md)

[**Outline of Editor & Correction Functions**](Outline%20of%20Editor%20&%20Correction%20Functions%20252033099726807ab48ad8e21443f008.md)

[OCR + HIL Ingestion Pipeline (Lane A) — v1.1](OCR%20+%20HIL%20Ingestion%20Pipeline%20(Lane%20A)%20%E2%80%94%20v1%201%2025303309972680a7ab51e3e005725c60.md)