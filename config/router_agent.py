#!/usr/bin/env python3
"""
Router Agent - Intelligent Query Routing
Analyzes user intent and routes to appropriate backend system
"""

import asyncio
import json
import sys
import logging
import httpx
import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueryType(Enum):
    CONVERSATIONAL = "conversational"  # Memory, history, context
    DOCUMENT = "document"              # Document upload, analysis
    BUSINESS = "business"              # Contract queries, search
    SYSTEM = "system"                  # Status, health checks

class RouterAgent:
    """Intelligent query routing agent"""
    
    def __init__(self):
        self.agent_api_base = "http://localhost:8000"
        self.cognee_api_base = "http://localhost:8001"  # Goose Memory DB
        
        # Intent detection patterns
        self.intent_patterns = {
            QueryType.CONVERSATIONAL: [
                r'what did we (talk|discuss|say)',
                r'remember (when|that|our)',
                r'(yesterday|last time|before|previous)',
                r'our (conversation|discussion|chat)',
                r'(context|history|background)',
                r'remind me (about|of)',
                r'what was (decided|agreed)',
            ],
            QueryType.DOCUMENT: [
                r'upload (this|a) (document|contract|file)',
                r'analyze (this|the) (document|contract)',
                r'process (this|the) (file|pdf|document)',
                r'extract (from|data from)',
                r'review (this|the) (contract|agreement)',
            ],
            QueryType.BUSINESS: [
                r'find (contracts|documents|agreements)',
                r'search (for|contracts|documents)',
                r'show (me )?(recent|all|latest)',
                r'(contracts|agreements|documents) (for|with|from)',
                r'(acme|company|client|vendor)',
                r'financial (terms|amounts|values)',
                r'legal (clauses|terms|conditions)',
            ],
            QueryType.SYSTEM: [
                r'(status|health|working)',
                r'system (status|check|health)',
                r'agent (status|system)',
                r'database (status|connection)',
                r'is .* (working|operational|running)',
            ]
        }
        
        self.tools = {
            "route_query": {
                "name": "route_query", 
                "description": "Route user queries to appropriate backend system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User query to route"},
                        "context": {"type": "string", "description": "Additional context", "default": ""}
                    },
                    "required": ["query"]
                }
            }
        }
    
    def analyze_intent(self, query: str) -> QueryType:
        """Analyze user query to determine intent"""
        query_lower = query.lower()
        
        # Score each intent type
        scores = {intent_type: 0 for intent_type in QueryType}
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    scores[intent_type] += 1
        
        # Return highest scoring intent, default to BUSINESS
        max_score = max(scores.values())
        if max_score == 0:
            return QueryType.BUSINESS  # Default for unclear queries
            
        return max(scores, key=scores.get)
    
    async def route_conversational(self, query: str) -> Dict[str, Any]:
        """Route to Goose Memory Database (Cognee)"""
        try:
            logger.info(f"Routing conversational query to Cognee: {query[:50]}...")
            
            # Call Cognee memory system
            async with httpx.AsyncClient() as client:
                # Simulate Cognee search call
                # In production, this would call actual Cognee API
                response = await client.post(
                    f"{self.cognee_api_base}/search",
                    json={"query": query, "limit": 5},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "source": "cognee_memory",
                        "type": "conversational",
                        "results": data.get("results", []),
                        "confidence": 0.9
                    }
                else:
                    return {
                        "source": "cognee_memory",
                        "type": "conversational", 
                        "results": ["Memory search temporarily unavailable"],
                        "confidence": 0.3
                    }
                    
        except Exception as e:
            logger.error(f"Cognee routing failed: {e}")
            return {
                "source": "cognee_memory",
                "type": "conversational",
                "results": [f"Memory system error: {str(e)}"],
                "confidence": 0.1
            }
    
    async def route_document(self, query: str, content: str = "") -> Dict[str, Any]:
        """Route document processing to Agent API"""
        try:
            logger.info(f"Routing document query to Agent API: {query[:50]}...")
            
            if content:
                # Document upload/analysis
                async with httpx.AsyncClient() as client:
                    payload = {
                        "content": content,
                        "filename": "user_document.txt",
                        "options": {
                            "useLegalBERT": True,
                            "trackLifecycle": True,
                            "extractEntities": True
                        }
                    }
                    
                    response = await client.post(
                        f"{self.agent_api_base}/api/analyze-document",
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "source": "agent_api",
                            "type": "document_analysis",
                            "results": data,
                            "confidence": 0.95
                        }
            
            return {
                "source": "agent_api",
                "type": "document",
                "results": ["Please provide document content for analysis"],
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Agent API routing failed: {e}")
            return {
                "source": "agent_api",
                "type": "document",
                "results": [f"Document processing error: {str(e)}"],
                "confidence": 0.1
            }
    
    async def route_business(self, query: str) -> Dict[str, Any]:
        """Route business queries to Agent API database"""
        try:
            logger.info(f"Routing business query to Agent API: {query[:50]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.agent_api_base}/api/documents?limit=10",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "source": "agent_api",
                        "type": "business_search",
                        "results": data,
                        "confidence": 0.85
                    }
                    
        except Exception as e:
            logger.error(f"Business query routing failed: {e}")
            
        return {
            "source": "agent_api", 
            "type": "business",
            "results": [f"Business query processing error: {str(e)}"],
            "confidence": 0.1
        }
    
    async def route_system(self, query: str) -> Dict[str, Any]:
        """Route system queries to status endpoints"""
        try:
            logger.info(f"Routing system query: {query[:50]}...")
            
            # Check both systems
            async with httpx.AsyncClient() as client:
                agent_response = await client.get(f"{self.agent_api_base}/api/system-status", timeout=10.0)
                
                results = {
                    "agent_system": "healthy" if agent_response.status_code == 200 else "unhealthy",
                    "cognee_memory": "checking..."  # Would check Cognee status
                }
                
                return {
                    "source": "system_status",
                    "type": "system",
                    "results": results,
                    "confidence": 0.9
                }
                
        except Exception as e:
            return {
                "source": "system_status",
                "type": "system", 
                "results": {"error": str(e)},
                "confidence": 0.1
            }
    
    async def route_query(self, query: str, context: str = "", content: str = "") -> str:
        """Main routing function"""
        try:
            # Analyze query intent
            intent = self.analyze_intent(query)
            logger.info(f"Query intent detected: {intent.value}")
            
            # Route to appropriate backend
            if intent == QueryType.CONVERSATIONAL:
                result = await self.route_conversational(query)
            elif intent == QueryType.DOCUMENT:
                result = await self.route_document(query, content)
            elif intent == QueryType.BUSINESS:
                result = await self.route_business(query)
            elif intent == QueryType.SYSTEM:
                result = await self.route_system(query)
            else:
                result = await self.route_business(query)  # Default fallback
            
            # Format response for Goose
            formatted_response = self.format_response(result, intent)
            return formatted_response
            
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return f"Routing error: {str(e)}"
    
    def format_response(self, result: Dict[str, Any], intent: QueryType) -> str:
        """Format routing result for Goose display"""
        source = result.get("source", "unknown")
        confidence = result.get("confidence", 0.0)
        results = result.get("results", {})
        
        response = f"**Query routed to: {source}** (Intent: {intent.value}, Confidence: {confidence:.1%})\n\n"
        
        if intent == QueryType.CONVERSATIONAL:
            response += "📝 **Memory Search Results:**\n"
            if isinstance(results, list):
                for i, item in enumerate(results[:3], 1):
                    response += f"{i}. {item}\n"
            else:
                response += "No relevant memories found.\n"
                
        elif intent == QueryType.DOCUMENT:
            if isinstance(results, dict) and "document_id" in results:
                response += "📄 **Document Analysis Complete:**\n"
                response += f"- Document ID: {results['document_id']}\n"
                response += f"- Confidence: {results['confidence_score']:.1%}\n"
                response += f"- Processing: {results['processing_method']}\n"
            else:
                response += "📄 **Document Processing:**\n"
                response += str(results)
                
        elif intent == QueryType.BUSINESS:
            response += "🏢 **Business Query Results:**\n"
            if isinstance(results, dict) and "documents" in results:
                docs = results["documents"][:3]
                for doc in docs:
                    response += f"- {doc.get('filename', 'Unknown')}\n"
            else:
                response += str(results)
                
        elif intent == QueryType.SYSTEM:
            response += "🔧 **System Status:**\n"
            if isinstance(results, dict):
                for key, value in results.items():
                    response += f"- {key}: {value}\n"
        
        return response
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
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
                        "capabilities": {"tools": {"listChanged": True}},
                        "serverInfo": {"name": "router-agent", "version": "1.0.0"}
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
                
                if tool_name == "route_query":
                    result = await self.route_query(
                        arguments.get("query", ""),
                        arguments.get("context", ""),
                        arguments.get("content", "")
                    )
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

async def main():
    """Main MCP server loop"""
    router = RouterAgent()
    logger.info("Starting Router Agent (Intelligent Query Routing)...")
    
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await router.handle_request(request)
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
        logger.info("Shutting down Router Agent...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())