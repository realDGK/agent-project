#!/usr/bin/env python3
"""
Agent System MCP Server
Bridges Goose to our PostgreSQL-based Agent Document Processing System
"""

import asyncio
import json
import sys
import logging
import httpx
from typing import Any, Dict, List, Optional
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentMCPServer:
    """MCP Server bridging Goose to our Agent API system"""
    
    def __init__(self):
        self.agent_api_base = "http://localhost:8000"
        self.tools = {
            "upload_document": {
                "name": "upload_document",
                "description": "Upload and analyze a document using the Agent system with LegalBERT",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Document content"},
                        "filename": {"type": "string", "description": "Document filename"},
                        "use_legal_bert": {"type": "boolean", "description": "Use LegalBERT analysis", "default": True},
                        "track_lifecycle": {"type": "boolean", "description": "Track contract lifecycle", "default": True},
                        "extract_entities": {"type": "boolean", "description": "Extract legal entities", "default": True}
                    },
                    "required": ["content", "filename"]
                }
            },
            "query_documents": {
                "name": "query_documents",
                "description": "Search and retrieve analyzed documents from the Agent system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or 'recent' for recent documents"},
                        "limit": {"type": "integer", "description": "Max results", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            "agent_status": {
                "name": "agent_status",
                "description": "Get Agent system status including database and AI services",
                "inputSchema": {"type": "object", "properties": {}}
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True}
                        },
                        "serverInfo": {
                            "name": "agent-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": list(self.tools.values())}
                }
            
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                if tool_name == "upload_document":
                    result = await self.upload_document(arguments)
                elif tool_name == "query_documents":
                    result = await self.query_documents(arguments.get("query", ""), arguments.get("limit", 10))
                elif tool_name == "agent_status":
                    result = await self.get_agent_status()
                else:
                    raise Exception(f"Unknown tool: {tool_name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            
            else:
                raise Exception(f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -1, "message": str(e)}
            }
    
    async def upload_document(self, arguments: Dict[str, Any]) -> str:
        """Upload document to Agent system for LegalBERT analysis"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "content": arguments.get("content", ""),
                    "filename": arguments.get("filename", ""),
                    "options": {
                        "useLegalBERT": arguments.get("use_legal_bert", True),
                        "trackLifecycle": arguments.get("track_lifecycle", True),
                        "extractEntities": arguments.get("extract_entities", True)
                    },
                    "priority": "normal"
                }
                
                response = await client.post(
                    f"{self.agent_api_base}/api/analyze-document",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format response for Goose
                    result = f"""Document Analysis Complete!

**Document:** {data['filename']}
**Processing Time:** {data['processing_time']:.2f}s
**Confidence Score:** {data['confidence_score']:.2f}
**Processing Method:** {data['processing_method']}
**Requires Review:** {'Yes' if data['requires_human_review'] else 'No'}

**Extracted Metadata:**
- Document Type: {data['extracted_metadata'].get('document_type', {}).get('primary', 'Unknown')}
- Parties: {len(data['extracted_metadata'].get('parties', []))} identified
- Financial Terms: {len(data['extracted_metadata'].get('financial_terms', []))} found
- Legal Terms: {', '.join(data['extracted_metadata'].get('legal_terms', {}).keys()) if data['extracted_metadata'].get('legal_terms') else 'None'}

**Document ID:** {data['document_id']}

The document has been stored in the PostgreSQL database and is available for future queries."""
                    
                    logger.info(f"Document uploaded successfully: {data['document_id']}")
                    return result
                else:
                    error_msg = f"Agent API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return f"Failed to upload document: {error_msg}"
                    
        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            return f"Failed to upload document: {str(e)}"
    
    async def query_documents(self, query: str, limit: int) -> str:
        """Query documents from Agent system"""
        try:
            async with httpx.AsyncClient() as client:
                if query.lower() == "recent":
                    response = await client.get(
                        f"{self.agent_api_base}/api/documents?limit={limit}",
                        timeout=30.0
                    )
                else:
                    # For now, just get recent documents
                    # TODO: Implement semantic search when available
                    response = await client.get(
                        f"{self.agent_api_base}/api/documents?limit={limit}",
                        timeout=30.0
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get('documents', [])
                    
                    if not documents:
                        return "No documents found in the database."
                    
                    # Format response for Goose
                    result = f"Found {len(documents)} documents:\n\n"
                    
                    for i, doc in enumerate(documents, 1):
                        result += f"**{i}. {doc['filename']}**\n"
                        result += f"   - Uploaded: {doc['created_at'][:16].replace('T', ' ')}\n"
                        result += f"   - Confidence: {doc['confidence_score']:.2f}\n"
                        result += f"   - Processing: {doc['processing_method']}\n"
                        result += f"   - Review Required: {'Yes' if doc['requires_human_review'] else 'No'}\n"
                        result += f"   - Document ID: {doc['document_id']}\n\n"
                    
                    logger.info(f"Retrieved {len(documents)} documents")
                    return result
                else:
                    error_msg = f"Agent API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return f"Failed to query documents: {error_msg}"
                    
        except Exception as e:
            logger.error(f"Failed to query documents: {str(e)}")
            return f"Failed to query documents: {str(e)}"
    
    async def get_agent_status(self) -> str:
        """Get Agent system status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.agent_api_base}/api/system-status",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = f"""Agent System Status: {data['status'].upper()}

**Database:** {data['database']['connection']}
- Recent documents: {data['database']['recent_documents']}

**AI Service:** {data['ai_service']['status']}
- Provider: {data['ai_service']['provider']}
- Model: {data['ai_service']['model']}

**Features Available:**
- Document Upload: {'✅' if data['features']['document_upload'] else '❌'}
- AI Analysis: {'✅' if data['features']['ai_analysis'] else '❌'}
- LegalBERT: {'✅' if data['features']['legal_bert_simulation'] else '❌'}
- Lifecycle Tracking: {'✅' if data['features']['lifecycle_tracking'] else '❌'}
- Entity Extraction: {'✅' if data['features']['entity_extraction'] else '❌'}
- Database Storage: {'✅' if data['features']['database_storage'] else '❌'}

**Timestamp:** {data['timestamp']}"""
                    
                    logger.info("Agent system status retrieved successfully")
                    return result
                else:
                    error_msg = f"Agent API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return f"Failed to get agent status: {error_msg}"
                    
        except Exception as e:
            logger.error(f"Failed to get agent status: {str(e)}")
            return f"Failed to get agent status: {str(e)}"

async def main():
    """Main MCP server loop"""
    server = AgentMCPServer()
    logger.info("Starting Agent MCP Server (Goose ↔ Agent API Bridge)...")
    
    try:
        while True:
            # Read JSON-RPC message from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {line.strip()}")
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -1, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        logger.info("Shutting down Agent MCP Server...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())