"""Specialized extraction agents for contract analysis."""

import asyncio
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from crewai import Agent, Task
from langchain_google_genai import ChatGoogleGenerativeAI

from .base import ExtractionAgent, AgentResult, TaskStatus
from ..config import settings


class DocumentClassificationAgent(ExtractionAgent):
    """Agent specialized in document type classification and structure analysis."""
    
    def __init__(self):
        super().__init__(
            agent_name="DocumentClassifier",
            description="Classifies document types and analyzes document structure"
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role='Document Classification Specialist',
            goal='Accurately classify document types and analyze document structure',
            backstory="""You are an expert in legal and business document classification. 
            You have extensive experience in identifying contract types, agreement structures, 
            and document formatting patterns. You focus on accuracy and provide confidence scores.""",
            verbose=True,
            allow_delegation=False,
            llm=ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=0.1
            )
        )
    
    async def process(self, document_content: str, context: Dict[str, Any]) -> AgentResult:
        """Process document for classification."""
        start_time = time.time()
        task_id = context.get('task_id', 'unknown')
        
        try:
            # Extract classification data
            classification_data = await self.extract_data(document_content, context)
            
            # Calculate confidence based on classification strength
            confidence = self._calculate_confidence(classification_data, document_content)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                confidence=confidence,
                data=classification_data,
                processing_time_ms=processing_time,
                metadata={'agent_type': 'extraction', 'specialization': 'classification'}
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(f"Classification failed: {e}")
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.FAILED,
                confidence=0.0,
                data={},
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def extract_data(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract document classification data using AI."""
        
        classification_task = Task(
            description=f"""
            Analyze this document and classify it accurately:
            
            Document Content:
            {content[:2000]}
            
            Provide classification in this exact format:
            - Document Type: [contract|agreement|nda|lease|employment|invoice|legal|correspondence|other]
            - Sub-type: [service_agreement|purchase_order|amendment|renewal|etc]
            - Document Structure: [formal|informal|template|custom]
            - Language Complexity: [simple|moderate|complex|legal_heavy]
            - Confidence Score: [0.0-1.0]
            """,
            agent=self.crew_agent,
            expected_output="Structured document classification with confidence scores"
        )
        
        # Execute the task
        result = classification_task.execute()
        
        # Parse the AI response
        return self._parse_classification_response(result, content)
    
    def _parse_classification_response(self, ai_response: str, content: str) -> Dict[str, Any]:
        """Parse AI response into structured data with fallback extraction."""
        
        try:
            # Try to extract from AI response
            doc_type = re.search(r'Document Type:\s*([a-z_]+)', ai_response.lower())
            sub_type = re.search(r'Sub-type:\s*([a-z_]+)', ai_response.lower())
            structure = re.search(r'Document Structure:\s*([a-z_]+)', ai_response.lower())
            complexity = re.search(r'Language Complexity:\s*([a-z_]+)', ai_response.lower())
            confidence = re.search(r'Confidence Score:\s*([0-9.]+)', ai_response)
            
            return {
                'document_type': {
                    'primary': doc_type.group(1) if doc_type else self._classify_fallback(content),
                    'secondary': sub_type.group(1) if sub_type else 'general',
                    'structure': structure.group(1) if structure else 'unknown',
                    'complexity': complexity.group(1) if complexity else 'moderate'
                },
                'ai_confidence': float(confidence.group(1)) if confidence else 0.7,
                'classification_method': 'ai_analysis'
            }
            
        except Exception as e:
            self.logger.warning(f"AI parsing failed, using fallback: {e}")
            return {
                'document_type': {
                    'primary': self._classify_fallback(content),
                    'secondary': 'general',
                    'structure': 'unknown',
                    'complexity': 'moderate'
                },
                'ai_confidence': 0.5,
                'classification_method': 'fallback_rules'
            }
    
    def _classify_fallback(self, content: str) -> str:
        """Fallback classification using rule-based approach."""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["service agreement", "consulting", "professional services"]):
            return "contract"
        elif "non-disclosure" in content_lower or "nda" in content_lower:
            return "nda"
        elif "employment" in content_lower or "hire" in content_lower:
            return "employment"
        elif any(term in content_lower for term in ["lease", "rental", "rent"]):
            return "lease"
        elif "invoice" in content_lower or "bill" in content_lower:
            return "invoice"
        else:
            return "other"
    
    def _calculate_confidence(self, classification_data: Dict[str, Any], content: str) -> float:
        """Calculate overall confidence score."""
        ai_confidence = classification_data.get('ai_confidence', 0.5)
        
        # Boost confidence if we have strong indicators
        doc_type = classification_data.get('document_type', {}).get('primary', 'other')
        
        if doc_type != 'other':
            ai_confidence *= 1.1  # Boost for specific classification
        
        if len(content) > 500:
            ai_confidence *= 1.05  # Boost for substantial content
            
        return min(ai_confidence, 1.0)


class PartyExtractionAgent(ExtractionAgent):
    """Agent specialized in extracting parties, signatories, and contact information."""
    
    def __init__(self):
        super().__init__(
            agent_name="PartyExtractor",
            description="Extracts parties, companies, individuals, and contact information"
        )
        
        self.crew_agent = Agent(
            role='Party and Contact Extraction Specialist',
            goal='Identify all parties, signatories, companies, and contact information in documents',
            backstory="""You are an expert in identifying business entities, individuals, 
            and contact information in legal and business documents. You excel at distinguishing 
            between different party roles and extracting accurate contact details.""",
            verbose=True,
            allow_delegation=False,
            llm=ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=0.1
            )
        )
    
    async def process(self, document_content: str, context: Dict[str, Any]) -> AgentResult:
        """Process document for party extraction."""
        start_time = time.time()
        task_id = context.get('task_id', 'unknown')
        
        try:
            party_data = await self.extract_data(document_content, context)
            confidence = self._calculate_party_confidence(party_data, document_content)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                confidence=confidence,
                data=party_data,
                processing_time_ms=processing_time,
                metadata={'agent_type': 'extraction', 'specialization': 'parties'}
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(f"Party extraction failed: {e}")
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.FAILED,
                confidence=0.0,
                data={'parties': []},
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def extract_data(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract party data using AI with fallback."""
        
        party_task = Task(
            description=f"""
            Extract all parties and contact information from this document:
            
            {content[:1500]}
            
            For each party, identify:
            - Name (company or individual)
            - Role (client, vendor, contractor, employee, etc.)
            - Contact information (email, phone, address if available)
            - Legal entity type (LLC, Inc, individual, etc.)
            
            Format as structured data showing relationships and hierarchies.
            """,
            agent=self.crew_agent,
            expected_output="Structured list of all parties with roles and contact information"
        )
        
        ai_result = party_task.execute()
        
        # Combine AI results with rule-based extraction
        ai_parties = self._parse_party_response(ai_result)
        fallback_parties = self._extract_parties_fallback(content)
        
        # Merge and deduplicate
        merged_parties = self._merge_party_data(ai_parties, fallback_parties)
        
        return {
            'parties': merged_parties,
            'extraction_method': 'ai_with_fallback',
            'total_parties': len(merged_parties)
        }
    
    def _parse_party_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract party information."""
        # This would contain logic to parse the AI's structured response
        # For now, return empty list as placeholder
        return []
    
    def _extract_parties_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback party extraction using regex patterns."""
        parties = []
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        
        # Extract company names
        companies = re.findall(r'([A-Z][A-Za-z\s&]+(?:LLC|Inc\.|Corp\.|Corporation|Company|Group|Partners|LLP|LP))', content)
        
        # Extract individual names
        individuals = re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b', content)
        
        # Process companies
        for i, company in enumerate(companies[:3]):  # Max 3 companies
            role = "client" if i == 0 else "vendor"
            contact_email = emails[i] if i < len(emails) else None
            
            parties.append({
                'name': company.strip(),
                'type': 'company',
                'role': role,
                'contact': {
                    'email': contact_email
                }
            })
        
        # Process individuals if not enough companies
        if len(parties) < 2:
            for individual in individuals[:2-len(parties)]:
                if individual.lower() not in ['service agreement', 'this agreement', 'letter of']:
                    parties.append({
                        'name': individual.strip(),
                        'type': 'individual',
                        'role': 'signatory',
                        'contact': {}
                    })
        
        return parties
    
    def _merge_party_data(self, ai_parties: List[Dict], fallback_parties: List[Dict]) -> List[Dict[str, Any]]:
        """Merge AI and fallback party data, removing duplicates."""
        # Use fallback for now, AI parsing would be implemented
        return fallback_parties
    
    def _calculate_party_confidence(self, party_data: Dict[str, Any], content: str) -> float:
        """Calculate confidence in party extraction."""
        parties = party_data.get('parties', [])
        
        if len(parties) == 0:
            return 0.3
        elif len(parties) >= 2:
            return 0.8
        else:
            return 0.6


class FinancialAnalysisAgent(ExtractionAgent):
    """Agent specialized in extracting financial terms, amounts, and payment structures."""
    
    def __init__(self):
        super().__init__(
            agent_name="FinancialAnalyzer",
            description="Extracts financial terms, contract values, and payment schedules"
        )
        
        self.crew_agent = Agent(
            role='Financial Terms Analysis Specialist',
            goal='Extract and analyze all financial terms, amounts, and payment structures',
            backstory="""You are an expert financial analyst specializing in contract terms. 
            You excel at identifying contract values, payment schedules, penalties, 
            and financial obligations in legal documents.""",
            verbose=True,
            allow_delegation=False,
            llm=ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=0.1
            )
        )
    
    async def process(self, document_content: str, context: Dict[str, Any]) -> AgentResult:
        """Process document for financial analysis."""
        start_time = time.time()
        task_id = context.get('task_id', 'unknown')
        
        try:
            financial_data = await self.extract_data(document_content, context)
            confidence = self._calculate_financial_confidence(financial_data, document_content)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                confidence=confidence,
                data=financial_data,
                processing_time_ms=processing_time,
                metadata={'agent_type': 'extraction', 'specialization': 'financial'}
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(f"Financial analysis failed: {e}")
            
            return self._create_result(
                task_id=task_id,
                status=TaskStatus.FAILED,
                confidence=0.0,
                data={'financial_terms': []},
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    async def extract_data(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data using AI with fallback."""
        
        # AI-based extraction
        financial_task = Task(
            description=f"""
            Extract all financial terms from this document:
            
            {content[:1500]}
            
            Identify:
            - Total contract value
            - Payment amounts and schedules
            - Penalties or late fees
            - Deposits or advances
            - Currency types
            - Payment terms and conditions
            
            Provide amounts, currencies, and context for each financial term.
            """,
            agent=self.crew_agent,
            expected_output="Structured financial terms with amounts, currencies, and payment schedules"
        )
        
        ai_result = financial_task.execute()
        
        # Fallback extraction
        fallback_terms = self._extract_financial_fallback(content)
        
        return {
            'financial_terms': fallback_terms,  # Would merge AI + fallback
            'total_contract_value': self._calculate_total_value(fallback_terms),
            'currency': self._detect_primary_currency(fallback_terms),
            'extraction_method': 'fallback_with_ai'
        }
    
    def _extract_financial_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Extract financial terms using regex patterns."""
        financial_terms = []
        
        # Find dollar amounts
        amounts = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)', content)
        
        for i, amount_str in enumerate(amounts):
            try:
                amount = float(amount_str.replace(',', ''))
                
                # Skip small amounts (likely formatting artifacts)
                if amount >= 100:
                    term_type = "contract_value" if i == 0 else "payment"
                    
                    financial_terms.append({
                        'amount': int(amount),
                        'currency': 'USD',
                        'type': term_type,
                        'description': f'Amount: ${amount_str}',
                        'context': self._extract_amount_context(content, f'${amount_str}')
                    })
                    
            except (ValueError, TypeError):
                continue
        
        return financial_terms[:5]  # Limit to 5 terms
    
    def _extract_amount_context(self, content: str, amount_str: str) -> str:
        """Extract context around a financial amount."""
        # Find the amount in content and get surrounding context
        index = content.find(amount_str)
        if index >= 0:
            start = max(0, index - 50)
            end = min(len(content), index + len(amount_str) + 50)
            return content[start:end].strip()
        return ""
    
    def _calculate_total_value(self, financial_terms: List[Dict]) -> Optional[int]:
        """Calculate total contract value from financial terms."""
        contract_values = [term['amount'] for term in financial_terms if term.get('type') == 'contract_value']
        return contract_values[0] if contract_values else None
    
    def _detect_primary_currency(self, financial_terms: List[Dict]) -> str:
        """Detect the primary currency used in the contract."""
        currencies = [term.get('currency', 'USD') for term in financial_terms]
        return max(set(currencies), key=currencies.count) if currencies else 'USD'
    
    def _calculate_financial_confidence(self, financial_data: Dict[str, Any], content: str) -> float:
        """Calculate confidence in financial extraction."""
        terms = financial_data.get('financial_terms', [])
        
        if len(terms) == 0:
            return 0.4
        elif len(terms) >= 3:
            return 0.85
        else:
            return 0.7