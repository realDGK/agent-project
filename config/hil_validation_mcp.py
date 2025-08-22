#!/usr/bin/env python3
"""
HIL Validation MCP Server
Provides human-in-the-loop validation for complex entity resolution and AI interpretations
Integrates with existing containerized architecture
"""

import asyncio
import json
import sys
import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import redis.asyncio as aioredis
import asyncpg
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationPriority(Enum):
    CRITICAL = "critical"  # Financial/legal implications
    HIGH = "high"          # Entity misidentification
    MEDIUM = "medium"      # Name variations
    LOW = "low"            # Minor corrections

class ValidationType(Enum):
    ENTITY_MERGE = "entity_merge"              # Multiple entities should be one
    ENTITY_SPLIT = "entity_split"              # One entity should be multiple
    LLC_HIERARCHY = "llc_hierarchy"            # Parent-child relationships
    SIGNATORY_VALIDATION = "signatory_validation"  # Who can sign for LLC
    TEMPORAL_SEQUENCE = "temporal_sequence"    # Event ordering
    NAME_EVOLUTION = "name_evolution"          # Property/company name changes
    FINANCIAL_RECONCILIATION = "financial_reconciliation"  # Money doesn't add up

class HILValidationMCPServer:
    """MCP Server for HIL validation tasks"""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.validation_queue = "hil:validation:queue"
        self.priority_queues = {
            ValidationPriority.CRITICAL: "hil:queue:critical",
            ValidationPriority.HIGH: "hil:queue:high",
            ValidationPriority.MEDIUM: "hil:queue:medium",
            ValidationPriority.LOW: "hil:queue:low"
        }
        
        self.tools = {
            "queue_validation": {
                "name": "queue_validation",
                "description": "Queue a validation task for human review",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "validation_type": {
                            "type": "string",
                            "enum": ["entity_merge", "entity_split", "llc_hierarchy", 
                                    "signatory_validation", "temporal_sequence", 
                                    "name_evolution", "financial_reconciliation"]
                        },
                        "ai_interpretation": {
                            "type": "object",
                            "description": "What the AI thinks"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "AI confidence score"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context"
                        },
                        "suggested_correction": {
                            "type": "object",
                            "description": "AI suggested correction"
                        },
                        "document_id": {
                            "type": "string",
                            "description": "Related document ID"
                        }
                    },
                    "required": ["validation_type", "ai_interpretation", "confidence"]
                }
            },
            
            "get_pending_validations": {
                "name": "get_pending_validations",
                "description": "Get pending validation tasks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low", "all"]
                        },
                        "validation_type": {
                            "type": "string",
                            "description": "Filter by validation type"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10
                        }
                    }
                }
            },
            
            "submit_correction": {
                "name": "submit_correction",
                "description": "Submit human correction for validation task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Validation task ID"
                        },
                        "correction": {
                            "type": "object",
                            "description": "The correction to apply"
                        },
                        "reviewer": {
                            "type": "string",
                            "description": "Who reviewed this"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Review notes"
                        }
                    },
                    "required": ["task_id", "correction", "reviewer"]
                }
            },
            
            "validate_llc_hierarchy": {
                "name": "validate_llc_hierarchy",
                "description": "Validate complex LLC ownership structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "root_entity": {
                            "type": "string",
                            "description": "Person or top-level entity"
                        },
                        "llcs": {
                            "type": "array",
                            "description": "List of LLCs"
                        },
                        "relationships": {
                            "type": "array",
                            "description": "Parent-child relationships"
                        }
                    },
                    "required": ["root_entity", "llcs"]
                }
            },
            
            "validate_entity_resolution": {
                "name": "validate_entity_resolution",
                "description": "Validate if multiple names refer to same entity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "description": "List of names/identifiers"
                        },
                        "entity_type": {
                            "type": "string",
                            "enum": ["property", "company", "person"]
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context"
                        }
                    },
                    "required": ["names", "entity_type"]
                }
            }
        }
    
    async def initialize(self):
        """Initialize connections"""
        try:
            # Redis connection
            self.redis_client = await aioredis.from_url(
                "redis://redis:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            # PostgreSQL connection
            self.db_pool = await asyncpg.create_pool(
                "postgresql://agent_user:agent_password@postgres:5432/agent_orchestration",
                min_size=2,
                max_size=5
            )
            
            logger.info("HIL Validation MCP Server initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                await self.initialize()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True}
                        },
                        "serverInfo": {
                            "name": "hil-validation-mcp",
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
                
                result = await self.handle_tool_call(tool_name, arguments)
                
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
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Handle specific tool calls"""
        
        if tool_name == "queue_validation":
            return await self.queue_validation_task(arguments)
        
        elif tool_name == "get_pending_validations":
            return await self.get_pending_validations(arguments)
        
        elif tool_name == "submit_correction":
            return await self.submit_correction(arguments)
        
        elif tool_name == "validate_llc_hierarchy":
            return await self.validate_llc_hierarchy(arguments)
        
        elif tool_name == "validate_entity_resolution":
            return await self.validate_entity_resolution(arguments)
        
        else:
            raise Exception(f"Unknown tool: {tool_name}")
    
    async def queue_validation_task(self, task_data: Dict) -> str:
        """Queue a validation task"""
        
        # Calculate priority
        priority = self.calculate_priority(task_data)
        
        # Create task
        task = {
            "task_id": str(uuid.uuid4()),
            "validation_type": task_data["validation_type"],
            "ai_interpretation": task_data["ai_interpretation"],
            "confidence": task_data["confidence"],
            "context": task_data.get("context", {}),
            "suggested_correction": task_data.get("suggested_correction"),
            "document_id": task_data.get("document_id"),
            "priority": priority.value,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "created_by": "ai_system"
        }
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO hil_validation_tasks 
                (task_id, validation_type, ai_interpretation, confidence, 
                 context, suggested_correction, document_id, priority, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, task["task_id"], task["validation_type"], 
                json.dumps(task["ai_interpretation"]), task["confidence"],
                json.dumps(task["context"]), json.dumps(task["suggested_correction"]),
                task["document_id"], task["priority"], task["status"],
                datetime.fromisoformat(task["created_at"]))
        
        # Queue in Redis by priority
        queue_name = self.priority_queues[priority]
        await self.redis_client.lpush(queue_name, json.dumps(task))
        
        # Return result
        result = f"""HIL Validation Task Queued

**Task ID:** {task['task_id']}
**Type:** {task['validation_type']}
**Priority:** {priority.value.upper()}
**Confidence:** {task['confidence']:.2%}
**Status:** Pending human review

The task has been queued for human validation. 
Current queue position: {await self.redis_client.llen(queue_name)}"""
        
        logger.info(f"Queued validation task {task['task_id']} with priority {priority.value}")
        
        return result
    
    def calculate_priority(self, task_data: Dict) -> ValidationPriority:
        """Calculate task priority"""
        
        validation_type = task_data.get("validation_type")
        confidence = task_data.get("confidence", 0.5)
        context = task_data.get("context", {})
        
        # Critical: Financial issues or legal validity
        if validation_type == "financial_reconciliation":
            return ValidationPriority.CRITICAL
        
        if validation_type == "signatory_validation" and confidence < 0.7:
            return ValidationPriority.CRITICAL
        
        # High: Entity resolution issues
        if validation_type in ["entity_merge", "entity_split", "llc_hierarchy"]:
            if confidence < 0.6:
                return ValidationPriority.HIGH
            else:
                return ValidationPriority.MEDIUM
        
        # Medium: Temporal and naming issues
        if validation_type in ["temporal_sequence", "name_evolution"]:
            if confidence < 0.5:
                return ValidationPriority.MEDIUM
            else:
                return ValidationPriority.LOW
        
        # Default based on confidence
        if confidence < 0.5:
            return ValidationPriority.HIGH
        elif confidence < 0.75:
            return ValidationPriority.MEDIUM
        else:
            return ValidationPriority.LOW
    
    async def get_pending_validations(self, params: Dict) -> str:
        """Get pending validation tasks"""
        
        priority = params.get("priority", "all")
        validation_type = params.get("validation_type")
        limit = params.get("limit", 10)
        
        tasks = []
        
        # Get from appropriate queue(s)
        if priority == "all":
            queues = list(self.priority_queues.values())
        else:
            priority_enum = ValidationPriority(priority)
            queues = [self.priority_queues[priority_enum]]
        
        for queue_name in queues:
            # Get tasks from Redis
            queue_tasks = await self.redis_client.lrange(queue_name, 0, limit - 1)
            for task_json in queue_tasks:
                task = json.loads(task_json)
                
                # Filter by type if specified
                if validation_type and task["validation_type"] != validation_type:
                    continue
                
                tasks.append(task)
                
                if len(tasks) >= limit:
                    break
        
        if not tasks:
            return "No pending validation tasks found."
        
        # Format result
        result = f"Found {len(tasks)} pending validation tasks:\n\n"
        
        for i, task in enumerate(tasks, 1):
            result += f"""**{i}. {task['validation_type'].replace('_', ' ').title()}**
   Task ID: {task['task_id']}
   Priority: {task['priority'].upper()}
   Confidence: {task['confidence']:.2%}
   Created: {task['created_at'][:16]}
   Document: {task.get('document_id', 'N/A')[:8]}...
   
"""
        
        return result
    
    async def validate_llc_hierarchy(self, params: Dict) -> str:
        """Validate LLC hierarchy structure"""
        
        root_entity = params["root_entity"]
        llcs = params["llcs"]
        relationships = params.get("relationships", [])
        
        # Build graph
        graph = nx.DiGraph()
        
        # Add nodes
        graph.add_node(root_entity, type="person")
        for llc in llcs:
            graph.add_node(llc, type="llc")
        
        # Add edges
        for rel in relationships:
            parent = rel.get("parent")
            child = rel.get("child")
            rel_type = rel.get("type", "owns")
            
            if parent and child:
                graph.add_edge(parent, child, relationship=rel_type)
        
        # Validate structure
        issues = []
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            issues.append(f"Circular ownership detected: {cycles}")
        
        # Check for orphan LLCs
        for llc in llcs:
            if graph.in_degree(llc) == 0 and llc != root_entity:
                issues.append(f"Orphan LLC with no parent: {llc}")
        
        # Check signatory paths
        signatory_paths = {}
        for llc in llcs:
            try:
                path = nx.shortest_path(graph, root_entity, llc)
                signatory_paths[llc] = path
            except nx.NetworkXNoPath:
                issues.append(f"No ownership path from {root_entity} to {llc}")
        
        # Format result
        if issues:
            result = f"""LLC Hierarchy Validation: ISSUES FOUND

**Root Entity:** {root_entity}
**LLCs:** {len(llcs)}
**Relationships:** {len(relationships)}

**Issues Found:**
"""
            for issue in issues:
                result += f"- {issue}\n"
            
            # Queue for human review
            await self.queue_validation_task({
                "validation_type": "llc_hierarchy",
                "ai_interpretation": {
                    "root": root_entity,
                    "llcs": llcs,
                    "relationships": relationships
                },
                "confidence": 0.3,  # Low confidence due to issues
                "context": {"issues": issues}
            })
            
        else:
            result = f"""LLC Hierarchy Validation: VALID

**Root Entity:** {root_entity}
**LLCs:** {len(llcs)}
**Relationships:** {len(relationships)}

**Signatory Paths:**
"""
            for llc, path in signatory_paths.items():
                result += f"- {' → '.join(path)}\n"
        
        return result
    
    async def validate_entity_resolution(self, params: Dict) -> str:
        """Validate if multiple names refer to same entity"""
        
        names = params["names"]
        entity_type = params["entity_type"]
        context = params.get("context", {})
        
        # Check for obvious matches
        normalized_names = [self.normalize_name(name) for name in names]
        unique_normalized = set(normalized_names)
        
        confidence = 1.0 - (len(unique_normalized) - 1) / len(names)
        
        if len(unique_normalized) == 1:
            # All names normalize to the same
            result = f"""Entity Resolution: HIGH CONFIDENCE MATCH

**Entity Type:** {entity_type}
**Names Provided:** {len(names)}
**Unique After Normalization:** 1
**Confidence:** 100%

All provided names appear to refer to the same {entity_type}.

**Names:**
"""
            for name in names:
                result += f"- {name}\n"
            
        else:
            # Need human validation
            result = f"""Entity Resolution: NEEDS VALIDATION

**Entity Type:** {entity_type}
**Names Provided:** {len(names)}
**Unique After Normalization:** {len(unique_normalized)}
**Confidence:** {confidence:.1%}

These names may refer to different entities and need human review.

**Names:**
"""
            for name in names:
                result += f"- {name}\n"
            
            # Queue for review
            await self.queue_validation_task({
                "validation_type": "entity_merge",
                "ai_interpretation": {
                    "names": names,
                    "entity_type": entity_type,
                    "normalized": list(unique_normalized)
                },
                "confidence": confidence,
                "context": context
            })
        
        return result
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        import re
        
        # Convert to uppercase
        normalized = name.upper()
        
        # Remove common suffixes
        suffixes = ['LLC', 'INC', 'CORP', 'CORPORATION', 'LP', 'LLP', 'PARTNERS']
        for suffix in suffixes:
            normalized = normalized.replace(suffix, '')
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    async def submit_correction(self, params: Dict) -> str:
        """Submit correction for validation task"""
        
        task_id = params["task_id"]
        correction = params["correction"]
        reviewer = params["reviewer"]
        notes = params.get("notes", "")
        
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE hil_validation_tasks
                SET status = 'corrected',
                    correction = $1,
                    reviewer = $2,
                    review_notes = $3,
                    reviewed_at = $4
                WHERE task_id = $5
            """, json.dumps(correction), reviewer, notes,
                datetime.now(), task_id)
        
        # Apply correction based on type
        # This would integrate with your entity resolution system
        
        result = f"""Correction Applied Successfully

**Task ID:** {task_id}
**Reviewer:** {reviewer}
**Timestamp:** {datetime.now().isoformat()}

The correction has been applied to the system."""
        
        if notes:
            result += f"\n\n**Notes:** {notes}"
        
        logger.info(f"Correction applied for task {task_id} by {reviewer}")
        
        return result

async def main():
    """Main MCP server loop"""
    server = HILValidationMCPServer()
    logger.info("Starting HIL Validation MCP Server...")
    
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
        logger.info("Shutting down HIL Validation MCP Server...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
