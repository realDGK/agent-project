"""
Containerized Document Processing Pipeline with CrewAI
Main orchestrator for document identification and routing
"""
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
import structlog

from src.app.agents.base import BaseAgent, AgentResult, TaskStatus
from src.app.agents.extractors import (
    DocumentClassificationAgent,
    PartyExtractionAgent,
    FinancialAnalysisAgent
)

logger = structlog.get_logger()

class DocumentIdentificationRouter:
    """
    First stage: Identify document type and route to appropriate extraction pipeline
    Uses the 350+ document types defined in config/prompts/document_types
    """
    
    def __init__(self):
        self.document_types_path = Path("/app/config/prompts/document_types")
        self.pre_prompt_path = Path("/app/config/prompts/Pre_prompt.txt")
        
        # Load pre-prompt
        with open(self.pre_prompt_path, 'r') as f:
            self.pre_prompt = f.read()
        
        # Load document type mappings
        self.document_types = self._load_document_types()
        
        # Initialize CrewAI agent for document identification
        self.identifier_agent = Agent(
            role='Document Type Identifier',
            goal='Accurately identify document type from 350+ real estate document categories',
            backstory="""You are an expert in real estate documentation with deep knowledge 
            of development, construction, legal, and financial documents. You can identify 
            any document type from title reports to CFD bonds to environmental assessments.""",
            verbose=True,
            allow_delegation=False,
            llm=ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1
            )
        )
        
        # Initialize routing agent
        self.router_agent = Agent(
            role='Document Router',
            goal='Route documents to the correct extraction pipeline based on type',
            backstory="""You determine which extraction agents should process each document 
            based on its type. You understand which agents specialize in financial terms, 
            parties, obligations, property details, and complex legal structures.""",
            verbose=True,
            allow_delegation=True,
            llm=ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1
            )
        )
    
    def _load_document_types(self) -> Dict[str, Dict]:
        """Load all document type definitions from the slug-based folders"""
        document_types = {}
        
        # Load the mapping file if it exists for reference
        mapping_file = Path("/app/config/directory_name_mapping.json")
        reverse_mapping = {}
        if mapping_file.exists():
            with open(mapping_file) as f:
                mapping_data = json.load(f)
                reverse_mapping = mapping_data.get('reverse_mappings', {})
        
        # Scan all directories in document_types folder
        for dir_path in self.document_types_path.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith('.'):
                dir_name = dir_path.name  # Now using slug format like "purchase-sale-agreement-psa"
                
                # Convert slug to readable name
                doc_name = dir_name.replace('-', ' ').title()
                
                # Look for specialist schema and other files
                specialist_schema_files = list(dir_path.glob("*specialist_schema.json"))
                schema_additions_files = list(dir_path.glob("*schema_additions.json"))
                few_shot_files = list(dir_path.glob("*few_shot_examples.txt"))
                
                # Load the schemas
                specialist_schema = None
                if specialist_schema_files:
                    specialist_schema = self._load_json(specialist_schema_files[0])
                
                schema_additions = None
                if schema_additions_files:
                    schema_additions = self._load_json(schema_additions_files[0])
                
                few_shot_examples = None
                if few_shot_files:
                    few_shot_examples = few_shot_files[0].read_text()
                
                document_types[dir_name] = {
                    'slug': dir_name,
                    'name': doc_name,
                    'folder': dir_name,
                    'specialist_schema': specialist_schema,
                    'schema_additions': schema_additions,
                    'few_shot_examples': few_shot_examples,
                    'original_name': reverse_mapping.get(dir_name, dir_name)
                }
        
        logger.info(f"Loaded {len(document_types)} document type definitions")
        return document_types
    
    def _load_json(self, file_path: Path) -> Optional[Dict]:
        """Load JSON file safely"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {e}")
            return None
    
    async def identify_document(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Identify document type using CrewAI agent
        """
        
        # Create identification task
        identification_task = Task(
            description=f"""
            Identify the document type from these categories:
            {self._get_document_type_list()}
            
            Document filename: {filename}
            Document content (first 2000 chars):
            {content[:2000]}
            
            Return:
            1. Document type ID (number)
            2. Document type name
            3. Confidence score (0-1)
            4. Key indicators that led to this classification
            """,
            agent=self.identifier_agent,
            expected_output="Document type identification with ID, name, confidence, and reasoning"
        )
        
        # Execute identification
        result = identification_task.execute()
        
        # Parse result
        doc_type_info = self._parse_identification_result(result, content)
        
        logger.info(f"Identified document as: {doc_type_info['name']} (slug: {doc_type_info.get('slug', 'unknown')}, Confidence: {doc_type_info['confidence']})")
        
        return doc_type_info
    
    def _get_document_type_list(self) -> str:
        """Get formatted list of document types for the agent"""
        type_list = []
        for slug, doc_info in sorted(self.document_types.items()):
            type_list.append(f"• {doc_info['name']} ({slug})")
        
        # Return first 50 most common + instruction to identify others
        common_types = type_list[:50]
        return "\n".join(common_types) + "\n\n(Plus 300+ other specialized document types)"
    
    def _parse_identification_result(self, result: str, content: str) -> Dict[str, Any]:
        """Parse the identification result from the agent"""
        import re
        
        # Try to extract document type slug from parentheses
        slug_match = re.search(r'\(([a-z\-]+)\)', result.lower())
        doc_slug = slug_match.group(1) if slug_match else None
        
        # If no slug found, try to find by name
        if not doc_slug:
            result_lower = result.lower()
            for slug, doc_info in self.document_types.items():
                if doc_info['name'].lower() in result_lower or slug in result_lower:
                    doc_slug = slug
                    break
        
        # Try to extract confidence
        conf_match = re.search(r'confidence:\s*([\d.]+)', result.lower())
        confidence = float(conf_match.group(1)) if conf_match else 0.7
        
        # Get document info from our registry
        if doc_slug and doc_slug in self.document_types:
            doc_info = self.document_types[doc_slug]
        else:
            doc_info = {
                'slug': 'unknown',
                'name': 'Unknown Document Type',
                'folder': 'unknown'
            }
        
        return {
            'slug': doc_info.get('slug', 'unknown'),
            'name': doc_info.get('name', 'Unknown'),
            'folder': doc_info.get('folder', 'unknown'),
            'confidence': confidence,
            'specialist_schema': doc_info.get('specialist_schema'),
            'schema_additions': doc_info.get('schema_additions'),
            'few_shot_examples': doc_info.get('few_shot_examples'),
            'reasoning': result
        }
    
    async def route_document(self, doc_type_info: Dict, content: str) -> Dict[str, List[str]]:
        """
        Route document to appropriate extraction agents based on type
        """
        
        routing_task = Task(
            description=f"""
            Document type: {doc_type_info['name']} (slug: {doc_type_info.get('slug', 'unknown')})
            
            Determine which extraction agents should process this document:
            
            Available agents:
            - PartyExtractor: Extracts parties, entities, signatories
            - FinancialAnalyzer: Extracts financial terms, amounts, payment structures
            - ObligationExtractor: Extracts obligations, deadlines, conditions
            - PropertyExtractor: Extracts property details, locations, parcels
            - LegalStructureAnalyzer: Analyzes complex legal structures, LLCs, ownership
            
            Return a list of agents that should process this document type.
            Consider that {doc_type_info['name']} documents typically contain:
            {self._get_typical_content(doc_type_info.get('slug', 'unknown'))}
            """,
            agent=self.router_agent,
            expected_output="List of extraction agents to use for this document type"
        )
        
        result = routing_task.execute()
        
        # Parse routing decision
        routing = self._parse_routing_result(result, doc_type_info)
        
        logger.info(f"Routing document to agents: {routing['agents']}")
        
        return routing
    
    def _get_typical_content(self, doc_slug: str) -> str:
        """Get typical content for a document type"""
        
        # Map document types to typical content
        content_map = {
            "purchase-sale-agreement-psa": "parties, purchase price, property description, closing terms",
            "letter-of-intent-loi": "parties, proposed terms, price, contingencies",
            "loan-agreement": "lender, borrower, loan amount, interest rate, collateral",
            "development-agreement": "developer, municipality, obligations, infrastructure, fees",
            "lease-agreement": "landlord, tenant, rent, term, maintenance responsibilities",
            "employment-agreement": "employer, employee, salary, benefits, termination terms",
            # Add more mappings as needed
        }
        
        return content_map.get(doc_slug, "various terms and conditions")
    
    def _parse_routing_result(self, result: str, doc_type_info: Dict) -> Dict[str, Any]:
        """Parse routing decision from agent"""
        
        agents = []
        
        # Check which agents were mentioned
        if 'party' in result.lower():
            agents.append('PartyExtractor')
        if 'financial' in result.lower() or 'amount' in result.lower():
            agents.append('FinancialAnalyzer')
        if 'obligation' in result.lower() or 'deadline' in result.lower():
            agents.append('ObligationExtractor')
        if 'property' in result.lower() or 'parcel' in result.lower():
            agents.append('PropertyExtractor')
        if 'llc' in result.lower() or 'structure' in result.lower():
            agents.append('LegalStructureAnalyzer')
        
        # Default routing based on document type if no specific agents identified
        if not agents:
            doc_slug = doc_type_info.get('slug', '')
            if doc_slug in ['purchase-sale-agreement-psa', 'letter-of-intent-loi', 'option-agreement']:
                agents = ['PartyExtractor', 'FinancialAnalyzer', 'PropertyExtractor']
            elif doc_slug in ['loan-agreement', 'promissory-note', 'construction-loan-agreement']:
                agents = ['PartyExtractor', 'FinancialAnalyzer', 'ObligationExtractor']
            elif doc_slug == 'development-agreement':
                agents = ['PartyExtractor', 'ObligationExtractor', 'PropertyExtractor']
            else:
                agents = ['PartyExtractor', 'FinancialAnalyzer']  # Default
        
        return {
            'agents': agents,
            'reasoning': result
        }


class ExtractionOrchestrator:
    """
    Main orchestration crew that coordinates all extraction agents
    """
    
    def __init__(self):
        self.router = DocumentIdentificationRouter()
        
        # Initialize extraction agents
        self.agents = {
            'DocumentClassifier': DocumentClassificationAgent(),
            'PartyExtractor': PartyExtractionAgent(),
            'FinancialAnalyzer': FinancialAnalysisAgent(),
            # Add more agents as they're built
        }
        
        # Supervisor agent to coordinate results
        self.supervisor = Agent(
            role='Extraction Supervisor',
            goal='Coordinate extraction results and ensure completeness',
            backstory="""You oversee the extraction process and ensure all agents 
            work together effectively. You resolve conflicts between agent outputs 
            and ensure the final extraction is complete and accurate.""",
            verbose=True,
            allow_delegation=False,
            llm=ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1
            )
        )
    
    async def process_document(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Main processing pipeline
        """
        
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting document processing: {filename} (Task: {task_id})")
        
        # Step 1: Identify document type
        doc_type_info = await self.router.identify_document(content, filename)
        
        # Step 2: Route to appropriate agents
        routing = await self.router.route_document(doc_type_info, content)
        
        # Step 3: Execute extraction with selected agents
        extraction_results = await self._execute_extractions(
            content, 
            routing['agents'], 
            {'task_id': task_id, 'doc_type': doc_type_info}
        )
        
        # Step 4: Consolidate results with supervisor
        final_result = await self._consolidate_results(
            extraction_results, 
            doc_type_info,
            content
        )
        
        # Add metadata
        final_result['metadata'] = {
            'task_id': task_id,
            'filename': filename,
            'document_type': doc_type_info,
            'routing': routing,
            'processing_time': (datetime.now() - start_time).total_seconds(),
            'agents_used': routing['agents']
        }
        
        logger.info(f"Document processing complete: {task_id}")
        
        return final_result
    
    async def _execute_extractions(
        self, 
        content: str, 
        agent_names: List[str], 
        context: Dict
    ) -> List[AgentResult]:
        """Execute extraction with selected agents"""
        
        results = []
        
        # Run agents in parallel
        tasks = []
        for agent_name in agent_names:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                task = agent.process(content, context)
                tasks.append(task)
        
        # Wait for all agents to complete
        if tasks:
            results = await asyncio.gather(*tasks)
        
        return results
    
    async def _consolidate_results(
        self, 
        extraction_results: List[AgentResult],
        doc_type_info: Dict,
        content: str
    ) -> Dict[str, Any]:
        """Consolidate results from multiple agents"""
        
        # Prepare data for supervisor
        agent_outputs = {}
        for result in extraction_results:
            if result.is_successful:
                agent_outputs[result.agent_name] = result.data
        
        # Create consolidation task
        consolidation_task = Task(
            description=f"""
            Consolidate extraction results from multiple agents for a {doc_type_info['name']} document.
            
            Agent outputs:
            {json.dumps(agent_outputs, indent=2)}
            
            {self.router.pre_prompt}
            
            Create a unified extraction that includes:
            1. All parties with complete information
            2. All financial terms with context
            3. All dates and deadlines
            4. Any obligations or conditions
            5. Property/asset details
            
            Resolve any conflicts between agent outputs by preferring:
            - More complete information over partial
            - Higher confidence scores
            - Specific values over generic
            
            Return as clean JSON matching the document schema.
            """,
            agent=self.supervisor,
            expected_output="Consolidated extraction results as JSON"
        )
        
        consolidated = consolidation_task.execute()
        
        # Parse consolidated result
        try:
            # Clean up response
            if '```json' in consolidated:
                consolidated = consolidated.split('```json')[1].split('```')[0]
            elif '```' in consolidated:
                consolidated = consolidated.split('```')[1].split('```')[0]
            
            result = json.loads(consolidated)
        except json.JSONDecodeError:
            logger.error("Failed to parse consolidated results")
            # Fallback to merging agent outputs
            result = self._merge_agent_outputs(agent_outputs)
        
        return result
    
    def _merge_agent_outputs(self, agent_outputs: Dict) -> Dict:
        """Fallback method to merge agent outputs"""
        
        merged = {
            'parties': [],
            'financial_terms': [],
            'dates': [],
            'obligations': [],
            'property': {},
            'discovered_entities': []
        }
        
        for agent_name, output in agent_outputs.items():
            if 'parties' in output:
                merged['parties'].extend(output['parties'])
            if 'financial_terms' in output:
                merged['financial_terms'].extend(output['financial_terms'])
            # Continue for other fields
        
        # Deduplicate
        merged['parties'] = self._deduplicate_list(merged['parties'])
        merged['financial_terms'] = self._deduplicate_list(merged['financial_terms'])
        
        return merged
    
    def _deduplicate_list(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate items from list"""
        seen = set()
        unique = []
        
        for item in items:
            # Create a hashable representation
            item_hash = json.dumps(item, sort_keys=True)
            if item_hash not in seen:
                seen.add(item_hash)
                unique.append(item)
        
        return unique


# Containerized service entry point
if __name__ == "__main__":
    """
    Entry point for containerized extraction service
    This would be the main process in the extraction container
    """
    
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="Document Extraction Service")
    
    # Initialize orchestrator
    orchestrator = ExtractionOrchestrator()
    
    class ExtractionRequest(BaseModel):
        content: str
        filename: str
        options: Dict[str, Any] = {}
    
    @app.post("/extract")
    async def extract_document(request: ExtractionRequest):
        """Main extraction endpoint"""
        try:
            result = await orchestrator.process_document(
                request.content, 
                request.filename
            )
            return result
        except Exception as e:
            logger.exception("Extraction failed")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "extraction-orchestrator"}
    
    @app.get("/document-types")
    async def get_document_types():
        """Get list of supported document types"""
        return orchestrator.router.document_types
    
    # Run the service
    uvicorn.run(app, host="0.0.0.0", port=8100)
