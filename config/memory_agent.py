#!/usr/bin/env python3
"""
Memory Agent - Background Conversation Monitoring
Extracts key decisions, takeaways, and maintains active memory system
"""

import asyncio
import json
import logging
import httpx
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Structure for memory entries"""
    id: str
    summary: str
    importance: float  # 0.0 to 1.0
    timestamp: str
    context: str
    document_pointers: List[str]  # References to main database
    tags: List[str]

class MemoryAgent:
    """Monitors conversations and maintains active memory"""
    
    def __init__(self):
        self.cognee_api_base = "http://localhost:8001"  # Memory DB
        self.agent_api_base = "http://localhost:8000"   # Document DB
        
        # Patterns for extracting important information
        self.decision_patterns = [
            r'(decided|agreed|concluded) (that|to)',
            r'(we will|shall|must|need to)',
            r'(action item|todo|task)',
            r'(deadline|due by|completion)',
            r'(approved|rejected|declined)',
        ]
        
        self.document_patterns = [
            r'(document|contract|agreement) (id|number|reference)',
            r'(uploaded|analyzed|processed)',
            r'(signed|executed|finalized)',
            r'(amendment|addendum|modification)',
        ]
        
        self.business_patterns = [
            r'(client|vendor|party|company) (.+)',
            r'(\$[\d,]+|\d+\s*(dollars|USD))',
            r'(contract value|total amount|payment)',
            r'(legal terms|governing law|jurisdiction)',
        ]
    
    def calculate_importance(self, text: str) -> float:
        """Calculate importance score for text"""
        importance = 0.0
        text_lower = text.lower()
        
        # Decision indicators
        for pattern in self.decision_patterns:
            if re.search(pattern, text_lower):
                importance += 0.3
        
        # Document references
        for pattern in self.document_patterns:
            if re.search(pattern, text_lower):
                importance += 0.2
        
        # Business terms
        for pattern in self.business_patterns:
            if re.search(pattern, text_lower):
                importance += 0.1
        
        # Length factor (longer discussions often more important)
        length_factor = min(len(text) / 500, 0.2)
        importance += length_factor
        
        return min(importance, 1.0)
    
    def extract_document_pointers(self, text: str) -> List[str]:
        """Extract references to documents in main database"""
        pointers = []
        
        # Look for document IDs
        doc_id_pattern = r'document.{0,10}(id|ID).{0,10}([a-f0-9\-]{8,})'
        matches = re.finditer(doc_id_pattern, text, re.IGNORECASE)
        for match in matches:
            pointers.append(match.group(2))
        
        # Look for filenames
        filename_pattern = r'([\w\-_]+\.(pdf|docx|doc|txt|contract))'
        matches = re.finditer(filename_pattern, text, re.IGNORECASE)
        for match in matches:
            pointers.append(f"filename:{match.group(1)}")
        
        return pointers
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        tags = []
        text_lower = text.lower()
        
        # Entity types
        if any(word in text_lower for word in ['contract', 'agreement']):
            tags.append('contract')
        if any(word in text_lower for word in ['client', 'customer']):
            tags.append('client')
        if any(word in text_lower for word in ['vendor', 'supplier']):
            tags.append('vendor')
        if any(word in text_lower for word in ['payment', 'financial', 'money', '$']):
            tags.append('financial')
        if any(word in text_lower for word in ['legal', 'law', 'jurisdiction']):
            tags.append('legal')
        if any(word in text_lower for word in ['decision', 'approved', 'rejected']):
            tags.append('decision')
        
        return tags
    
    def create_summary(self, text: str) -> str:
        """Create concise summary of key points"""
        # Simple extractive summary for key sentences
        sentences = text.split('.')
        key_sentences = []
        
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            # Score sentence importance
            score = 0
            sentence_lower = sentence.lower()
            
            # Decision indicators
            for pattern in self.decision_patterns:
                if re.search(pattern, sentence_lower):
                    score += 2
            
            # Document/business terms
            for pattern in self.document_patterns + self.business_patterns:
                if re.search(pattern, sentence_lower):
                    score += 1
            
            if score > 0:
                key_sentences.append((sentence, score))
        
        # Sort by score and take top 3
        key_sentences.sort(key=lambda x: x[1], reverse=True)
        summary_sentences = [sent[0] for sent in key_sentences[:3]]
        
        return '. '.join(summary_sentences) + '.' if summary_sentences else text[:200] + '...'
    
    async def process_conversation(self, conversation: str, context: str = "") -> Optional[MemoryEntry]:
        """Process conversation and extract memory-worthy information"""
        try:
            # Calculate importance
            importance = self.calculate_importance(conversation)
            
            # Skip if not important enough
            if importance < 0.1:
                return None
            
            # Extract components
            summary = self.create_summary(conversation)
            pointers = self.extract_document_pointers(conversation)
            tags = self.extract_tags(conversation)
            
            # Create unique ID
            entry_id = hashlib.md5(f"{conversation[:100]}{datetime.now().isoformat()}".encode()).hexdigest()
            
            memory_entry = MemoryEntry(
                id=entry_id,
                summary=summary,
                importance=importance,
                timestamp=datetime.now().isoformat(),
                context=context,
                document_pointers=pointers,
                tags=tags
            )
            
            logger.info(f"Created memory entry: importance={importance:.2f}, tags={tags}")
            return memory_entry
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return None
    
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory entry in Cognee database"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "id": entry.id,
                    "content": entry.summary,
                    "metadata": {
                        "importance": entry.importance,
                        "timestamp": entry.timestamp,
                        "context": entry.context,
                        "document_pointers": entry.document_pointers,
                        "tags": entry.tags,
                        "type": "memory_entry"
                    }
                }
                
                # Store in Cognee memory database
                response = await client.post(
                    f"{self.cognee_api_base}/store",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Memory entry stored successfully: {entry.id}")
                    return True
                else:
                    logger.warning(f"Failed to store memory entry: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    async def monitor_conversation(self, conversation_text: str, user_id: str = "default") -> Dict[str, Any]:
        """Main monitoring function called by Goose"""
        try:
            # Process the conversation
            memory_entry = await self.process_conversation(conversation_text)
            
            if memory_entry:
                # Store in memory database
                success = await self.store_memory(memory_entry)
                
                return {
                    "status": "processed",
                    "memory_created": success,
                    "importance": memory_entry.importance,
                    "summary": memory_entry.summary,
                    "tags": memory_entry.tags,
                    "document_pointers": len(memory_entry.document_pointers)
                }
            else:
                return {
                    "status": "skipped",
                    "reason": "below_importance_threshold"
                }
                
        except Exception as e:
            logger.error(f"Error monitoring conversation: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory database for relevant entries"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.cognee_api_base}/search",
                    json={"query": query, "limit": limit, "type": "memory_entry"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.cognee_api_base}/stats", timeout=10.0)
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            
        return {"status": "unavailable", "error": str(e)}

# Singleton instance for background monitoring
memory_agent = MemoryAgent()

async def monitor_goose_conversation(text: str, user_id: str = "default") -> Dict[str, Any]:
    """Function to be called by Goose for conversation monitoring"""
    return await memory_agent.monitor_conversation(text, user_id)

async def search_goose_memory(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Function to search memory for Goose"""
    return await memory_agent.search_memory(query, limit)

if __name__ == "__main__":
    # Test the memory agent
    async def test_memory():
        test_conversation = """
        User: I want to upload this contract for Acme Corp. The total value is $500,000.
        Agent: Document uploaded successfully with ID: doc_12345. Analysis shows high-value contract.
        User: Great! We decided to approve this contract. Set the deadline for signature to next Friday.
        Agent: Noted. Contract approved with signature deadline of next Friday.
        """
        
        result = await memory_agent.monitor_conversation(test_conversation)
        print(f"Memory processing result: {result}")
        
    asyncio.run(test_memory())