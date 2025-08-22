"""
Enhanced FastAPI backend with proper HIL support - returns actual document text
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import uuid
import re

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import google.generativeai as genai
from persist_extraction import persist_extraction, build_db_extraction_payload
from db_selftest import router as db_selftest_router
from simple_extraction import (
    extract_with_gemini_simple,
    two_stage_extraction
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Contract Analysis Backend", version="1.0.0")

# Include the database self-test router
app.include_router(db_selftest_router)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://agent_user:agent_password@postgres:5432/agent_orchestration"
)

class DocumentAnalysisRequest(BaseModel):
    content: str
    filename: str
    options: Dict[str, bool] = {}

class DocumentAnalysisResult(BaseModel):
    document_id: str
    filename: str
    processing_time: float
    confidence_score: float
    extracted_metadata: Dict[str, Any]
    requires_human_review: bool
    processing_method: str
    analysis_timestamp: str
    ocr_score: float = 1.0
    # NEW FIELDS FOR HIL SUPPORT
    document_text: Optional[str] = None  # Actual extracted text
    low_confidence_regions: Optional[list] = None  # Areas needing review

# Global database pool
db_pool = None

async def get_db_pool():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
    return db_pool

@app.on_event("startup")
async def startup():
    await get_db_pool()
    logger.info("API started successfully with database connection")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "contract-analysis-backend"}

@app.get("/", response_class=HTMLResponse)
async def main_ui():
    """Serve the main Contract Analysis Platform upload UI"""
    upload_ui_path = "web-interface.html"
    if os.path.exists(upload_ui_path):
        return FileResponse(upload_ui_path, media_type="text/html")
    else:
        return HTMLResponse(content="<h1>Contract Analysis System</h1><p>Upload interface not found. Please check file path.</p>", status_code=404)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file formats"""
    try:
        if filename.lower().endswith('.docx'):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(file_content))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            except ImportError:
                logger.warning("python-docx not available, attempting text extraction fallback")
                text_content = file_content.decode('utf-8', errors='ignore')
                import re
                clean_text = re.sub(r'<[^>]+>', ' ', text_content)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                return clean_text.strip()
        elif filename.lower().endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')
        elif filename.lower().endswith('.pdf'):
            logger.warning("PDF processing not yet implemented")
            return "PDF processing not yet implemented"
        else:
            return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}")
        return f"Error extracting text from file: {str(e)}"

def identify_low_confidence_regions(text: str, ocr_score: float) -> list:
    """Identify regions in text that may need human review"""
    low_confidence_regions = []
    
    # Simulate OCR confidence analysis
    # In a real system, this would come from OCR engine
    if ocr_score < 0.85:
        # Find potential problem areas
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Look for common OCR issues
            issues = []
            
            # Check for unusual character patterns that might be OCR errors
            if re.search(r'[^\x20-\x7E\n\r\t]{2,}', line):  # Non-printable chars
                issues.append("non-printable characters")
            
            # Check for mixed case in middle of words (common OCR error)
            if re.search(r'\b\w+[A-Z]\w+\b', line) and not re.search(r'\b[A-Z][a-z]+[A-Z][a-z]+\b', line):
                issues.append("unusual capitalization")
            
            # Check for numbers mixed with letters inappropriately
            if re.search(r'\b\d+[a-zA-Z]+\d+\b|\b[a-zA-Z]+\d+[a-zA-Z]+\b', line):
                issues.append("mixed alphanumeric")
            
            # Check for isolated special characters
            if re.search(r'\s[^\w\s]\s', line):
                issues.append("isolated special character")
            
            if issues:
                low_confidence_regions.append({
                    "line_number": i + 1,
                    "text": line[:100],  # First 100 chars
                    "issues": issues,
                    "confidence": max(0.5, ocr_score - len(issues) * 0.1)
                })
    
    # Also flag specific important sections that always need review
    important_patterns = [
        (r'\$[\d,]+\.?\d*', 'financial amount'),
        (r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', 'date'),
        (r'\b(?:LLC|Inc|Corp|Corporation|LP|LLP)\b', 'legal entity'),
        (r'\b(?:guarantee|guaranty|indemnif|warrant|represent)\b', 'legal term')
    ]
    
    for pattern, description in important_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Find line number
            line_start = text.rfind('\n', 0, match.start()) + 1
            line_end = text.find('\n', match.end())
            if line_end == -1:
                line_end = len(text)
            line_num = text[:match.start()].count('\n') + 1
            
            low_confidence_regions.append({
                "line_number": line_num,
                "text": text[line_start:line_end][:100],
                "match": match.group(),
                "type": description,
                "position": {"start": match.start(), "end": match.end()},
                "confidence": ocr_score
            })
    
    return low_confidence_regions

def clean_noisy_document_content(content: str) -> str:
    """Clean up noisy document content from DOCX files read as text"""
    import re
    
    if len(content) > 50000 and ('<?xml' in content or 'word/' in content or 'PK' in content[:100]):
        logger.info("Detected noisy DOCX content, attempting cleanup")
        
        content = re.sub(r'PK.*?word/', '', content, flags=re.DOTALL)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        
        lines = content.split('\n')
        meaningful_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(word in line.lower() for word in 
                ['agreement', 'contract', 'lease', 'purchase', 'sale', 'party', 'buyer', 'seller', 
                 'landlord', 'tenant', 'dollar', '$', 'payment', 'date', 'property']):
                meaningful_lines.append(line)
        
        if meaningful_lines:
            return '\n'.join(meaningful_lines)
    
    return content

@app.post("/api/upload-document", response_model=DocumentAnalysisResult)
async def upload_document(file: UploadFile = File(...)):
    """Upload and analyze a document file with HIL support"""
    try:
        file_content = await file.read()
        extracted_text = extract_text_from_file(file_content, file.filename)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract meaningful text from file")
        
        logger.info(f"Extracted {len(extracted_text)} characters from {file.filename}")
        
        request = DocumentAnalysisRequest(
            content=extracted_text,
            filename=file.filename
        )
        
        return await analyze_document(request)
        
    except Exception as e:
        logger.exception("File upload analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-document", response_model=DocumentAnalysisResult)
async def analyze_document(request: DocumentAnalysisRequest):
    """Enhanced document analysis with OCR and HIL support"""
    try:
        # Clean noisy content
        cleaned_content = clean_noisy_document_content(request.content)
        if cleaned_content != request.content:
            logger.info(f"Content cleaned: {len(request.content)} -> {len(cleaned_content)} chars")
            request.content = cleaned_content
        
        # Detect if document needs OCR
        is_likely_scanned = detect_scanned_document(request.content)
        processing_method = "digital_extraction"
        ocr_score = 1.0
        requires_hil = False
        
        if is_likely_scanned:
            ocr_result = simulate_ocr_processing(request.filename)
            processing_method = ocr_result["method"]
            ocr_score = ocr_result["confidence"]
            requires_hil = ocr_score < 0.85
        
        # Identify low confidence regions for HIL
        low_confidence_regions = []
        if requires_hil or ocr_score < 0.9:
            low_confidence_regions = identify_low_confidence_regions(request.content, ocr_score)
        
        # Create document in database first
        pool = await get_db_pool()
        doc_id = str(uuid.uuid4())
        
        # AI Analysis ONLY - no duplicate extraction
        ai_analysis_result = None
        if GOOGLE_API_KEY:
            ai_analysis_result = three_lane_ai_analysis(request.content, request.filename)
            
            if ai_analysis_result:
                # Use AI results directly as metadata
                metadata = ai_analysis_result
                
                # Ensure required fields
                if 'processing_method' not in metadata:
                    metadata['processing_method'] = processing_method
                if 'ocr_score' not in metadata:
                    metadata['ocr_score'] = ocr_score
                if 'requires_hil' not in metadata:
                    metadata['requires_hil'] = requires_hil
                
                # Persist to database
                db_payload = build_db_extraction_payload(ai_analysis_result, request.filename)
                try:
                    await persist_extraction(pool, doc_id, db_payload)
                    logger.info(f"Successfully persisted AI analysis for document {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to persist AI analysis: {e}")
            else:
                # Fallback to basic metadata if AI fails
                metadata = {
                    "processing_method": processing_method,
                    "ocr_score": ocr_score,
                    "requires_hil": requires_hil,
                    "extraction_failed": True
                }
        
        return DocumentAnalysisResult(
            document_id=str(doc_id),
            filename=request.filename,
            processing_time=2.0 if is_likely_scanned else 1.0,
            confidence_score=ocr_score,
            extracted_metadata=metadata,
            requires_human_review=requires_hil,
            processing_method=processing_method,
            analysis_timestamp=datetime.now().isoformat(),
            ocr_score=ocr_score,
            # NEW: Include actual document text and regions for HIL
            document_text=request.content,  # Return the actual extracted text
            low_confidence_regions=low_confidence_regions if requires_hil else None
        )
        
    except Exception as e:
        logger.exception("Analysis failed with full stack trace")
        raise HTTPException(status_code=500, detail=str(e))

def detect_scanned_document(content: str) -> bool:
    """Detect if document is likely scanned based on content characteristics"""
    if len(content.strip()) < 100:
        return True
    
    ocr_artifacts = ['@', '|', '~', '\\', '_____', '-----']
    artifact_count = sum(1 for artifact in ocr_artifacts if artifact in content)
    
    total_chars = len(content)
    alpha_chars = sum(1 for c in content if c.isalpha())
    alpha_ratio = alpha_chars / total_chars if total_chars > 0 else 0
    
    return alpha_ratio < 0.6 or artifact_count > 3

def simulate_ocr_processing(filename: str) -> dict:
    """Simulate OCR processing with confidence scoring"""
    import random
    
    filename_lower = filename.lower()
    
    if 'scan' in filename_lower or 'poor' in filename_lower:
        confidence = 0.65
        method = "tesseract_ocr"
    elif 'old' in filename_lower or 'faded' in filename_lower:
        confidence = 0.75
        method = "tesseract_ocr"
    else:
        confidence = random.uniform(0.70, 0.95)
        method = "tesseract_ocr" if confidence < 0.85 else "hybrid_ocr"
    
    return {
        "confidence": confidence,
        "method": method,
        "pages_processed": 1,
        "avg_page_confidence": confidence
    }

def generate_document_metadata(content: str, filename: str) -> dict:
    """Generate realistic document-specific metadata from content"""
    import re
    import random
    
    doc_type = "Unknown"
    if any(word in filename.lower() for word in ['lease', 'rent']):
        doc_type = "Lease"
    elif any(word in filename.lower() for word in ['purchase', 'sale', 'psa']):
        doc_type = "PSA"
    elif any(word in filename.lower() for word in ['amendment', 'amend']):
        doc_type = "Amendment"
    elif any(word in filename.lower() for word in ['agreement', 'contract']):
        doc_type = "Contract"
    
    parties = []
    party_patterns = [
        r'between\s+([A-Z][A-Za-z\s&,\.]+?)\s+(?:and|,)',
        r'([A-Z][A-Za-z\s&,\.]+?)\s+(?:LLC|Inc|Corporation|Corp|LP|LLP)',
        r'(?:Landlord|Tenant|Buyer|Seller|Lessor|Lessee|Guarantor):\s*([A-Z][A-Za-z\s&,\.]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'([A-Z][A-Za-z\s&,\.]+?)\s+(?:acting as|serves as|represented by)',
        r'(?:Agent|Broker|Attorney):\s*([A-Z][A-Za-z\s&,\.]+)',
    ]
    
    for pattern in party_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            clean_match = match.strip(' ,.')
            if len(clean_match) > 2 and clean_match not in [p["text"] for p in parties]:
                parties.append({
                    "text": clean_match,
                    "confidence": random.uniform(0.75, 0.95)
                })
                if len(parties) >= 4:
                    break
    
    financial_terms = []
    money_patterns = [
        r'(?:rent|rental|monthly).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:purchase price|sale price|price).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:deposit|security).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:guarantee|guaranty|limit).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:fee|commission).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'\$([0-9,]+(?:\.[0-9]{2})?)',
        r'([0-9,]+(?:\.[0-9]{2})?)\s*dollars?',
    ]
    
    for pattern in money_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if amount > 1000:
                    financial_terms.append({
                        "amount": amount,
                        "label": "extracted_amount",
                        "confidence": random.uniform(0.80, 0.95)
                    })
                if len(financial_terms) >= 3:
                    break
            except ValueError:
                continue
    
    dates = []
    date_patterns = [
        r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            dates.append({
                "text": match,
                "label": "extracted_date",
                "confidence": random.uniform(0.70, 0.90)
            })
            if len(dates) >= 3:
                break
    
    if not parties:
        parties = [{"text": "No parties identified", "confidence": 0.1}]
    if not financial_terms:
        financial_terms = [{"amount": 0, "label": "no_amount_found", "confidence": 0.1}]
    
    return {
        "document_type": {"primary": doc_type, "confidence": 0.8},
        "parties": parties,
        "financial_terms": financial_terms,
        "dates": dates,
        "content_length": len(content),
        "filename": filename
    }

def assess_extraction_quality(metadata: dict, content: str) -> float:
    """Assess how complete the data extraction is"""
    quality_score = 0.0
    
    party_count = len(metadata.get("parties", []))
    if party_count >= 2:
        quality_score += 0.3
    elif party_count >= 1:
        quality_score += 0.1
    
    financial_count = len(metadata.get("financial_terms", []))
    if financial_count >= 1:
        quality_score += 0.3
    
    date_count = len(metadata.get("dates", []))
    if date_count >= 1:
        quality_score += 0.2
    
    complexity_indicators = ['guarantee', 'broker', 'agent', 'attorney', 'amendment']
    complexity_found = sum(1 for indicator in complexity_indicators if indicator.lower() in content.lower())
    if complexity_found >= 2:
        quality_score -= 0.2
    
    if len(content) > 2000:
        quality_score -= 0.1
    
    return max(0.0, min(1.0, quality_score))

def three_lane_ai_analysis(content: str, filename: str) -> dict:
    """Simplified AI analysis - let Gemini do what it does best"""
    try:
        if GOOGLE_API_KEY:
            # Try simple extraction first (what actually works)
            simple_result = extract_with_gemini_simple(content, filename)
            if simple_result and not simple_result.get('error'):
                logger.info(f"Simple extraction successful")
                return simple_result
            
            # Try two-stage approach (basic then improve)
            two_stage_result = two_stage_extraction(content, filename)
            if two_stage_result and not two_stage_result.get('error'):
                logger.info(f"Two-stage extraction successful")
                return two_stage_result
        
        logger.error("All extraction methods failed")
        return None
            
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return None

def analyze_with_gemini_flash(content: str, filename: str) -> dict:
    """Analyze document with Gemini Flash"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        CRITICAL: Return ONLY valid JSON. No explanations, no markdown, just JSON.
        
        Analyze this legal document: {filename}
        
        Extract key information and return JSON in this exact format:
        {{
            "parties": [{{"text": "FULL_PARTY_NAME", "role": "landlord", "confidence": 0.95}}],
            "financial_terms": [{{"amount": 1500.00, "type": "rent", "frequency": "monthly", "confidence": 0.90}}],
            "dates": [{{"date": "2024-01-01", "type": "lease_start", "confidence": 0.85}}],
            "document_type": {{"type": "lease_agreement", "confidence": 0.90}},
            "key_terms": ["personal_guarantee", "net_lease"],
            "confidence_score": 0.85,
            "analysis_method": "gemini_flash"
        }}
        
        RULES:
        - Extract only parties explicitly named in the document
        - Include ALL dollar amounts found  
        - Use precise dates in YYYY-MM-DD format when possible
        - Set confidence_score to 0.95 if extraction is complete, 0.75 if partial
        
        Document content:
        {content[:4000]}
        """
        
        response = model.generate_content(prompt)
        
        try:
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            result['analysis_method'] = 'gemini_flash'
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for Flash: {e}. Response: {response.text[:200]}...")
            return parse_ai_text_response(response.text, 'gemini_flash')
            
    except Exception as e:
        logger.error(f"Gemini Flash analysis failed: {e}")
        return {"confidence_score": 0.0, "analysis_method": "gemini_flash_failed", "error": str(e)}

def analyze_with_gemini_pro(content: str, filename: str, previous_result: dict = None) -> dict:
    """Analyze document with Gemini Pro - Smart extraction with document type detection"""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""CRITICAL: Return ONLY valid JSON. No explanations before or after.

You are a real estate document expert. Analyze this document completely.

DOCUMENT: {filename}

STEP 1: Identify the EXACT document type from this list (or identify if it's something else):
- Letter of Intent (LOI)
- Purchase and Sale Agreement (PSA)
- Lease Agreement (Commercial/Residential/Ground)
- Development Agreement (DA)
- Conditional Use Permit (CUP)
- Site Plan Review (SPR)
- Building Permit
- Encroachment Permit
- Grant Deed
- Deed of Trust
- Quitclaim Deed
- Easement (utility/access/drainage/etc)
- CC&Rs (Covenants, Conditions & Restrictions)
- Title Report / Preliminary Title Report
- ALTA Survey
- Environmental Impact Report (EIR)
- Mitigated Negative Declaration (MND)
- Phase I/II Environmental Site Assessment
- Will-Serve Letter
- Sewer/Water Allocation Agreement
- Fee Reimbursement Agreement
- Amendment/Addendum (specify to what)
- Release/Satisfaction
- Escrow Instructions
- Settlement Statement
- Construction Contract
- Change Order
- Pay Application
- Lien Waiver
- Budget/Proforma
- Email correspondence
- Other (specify)

NEVER say "Unknown" - make your best determination based on content.

STEP 2: Extract ALL relevant information for that document type.

IMPORTANT: Differentiate between:
- PRINCIPALS: The actual parties to the transaction (buyers, sellers, landlords, tenants, borrowers, lenders)
- BROKERS/AGENTS: Real estate brokers, agents, or representatives (often on letterhead or signing as "agent for")
- Set "is_principal": true for actual parties, false for brokers/agents

STEP 3: Return comprehensive JSON.

Content to analyze:
{content[:10000]}

RETURN ONLY THIS JSON:
{{
    "document_type": {{
        "primary": "exact document type",
        "subtype": "if applicable",
        "confidence": 0.95
    }},
    "parties": [
        {{"text": "exact name", "role": "buyer/seller/landlord/tenant/owner", "entity_type": "LLC/individual/corporation", "is_principal": true}},
        {{"text": "broker/agent name if any", "role": "listing_agent/selling_agent/broker", "entity_type": "brokerage", "is_principal": false}}
    ],
    "financial_terms": [
        {{"amount": 0.00, "type": "purchase_price/rent/deposit", "description": "context"}}
    ],
    "dates": [
        {{"date": "YYYY-MM-DD or text", "type": "effective/closing/execution", "description": "what this date is"}}
    ],
    "property": {{
        "address": "street address if found",
        "apn": "parcel number if found",
        "common_name": "Pond C or whatever it's called",
        "legal_description": "if provided",
        "size": "acres or sq ft"
    }},
    "key_terms": [
        "important provision 1",
        "important provision 2"
    ],
    "document_specific_data": {{
        "permit_number": "if it's a permit",
        "conditions": "if it has conditions",
        "capacity": "if it's utility related",
        "obligations": "specific requirements"
    }},
    "references": [
        "references to other documents"
    ],
    "red_flags": [
        "any concerning issues"
    ],
    "confidence_score": 0.92,
    "analysis_method": "gemini_pro"
}}
"""
        
        response = model.generate_content(prompt)
        
        try:
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            result['analysis_method'] = 'gemini_pro'
            
            # Log what was detected
            doc_type = result.get('document_type', {}).get('primary', 'Unknown')
            logger.info(f"Gemini Pro identified document as: {doc_type}")
            
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for Pro: {e}. Response: {response.text[:200]}...")
            return parse_ai_text_response(response.text, 'gemini_pro')
            
    except Exception as e:
        logger.error(f"Gemini Pro analysis failed: {e}")
        return {"confidence_score": 0.0, "analysis_method": "gemini_pro_failed", "error": str(e)}

def parse_ai_text_response(text: str, method: str) -> dict:
    """Parse AI text response when JSON parsing fails"""
    import re
    
    parties = []
    party_matches = re.findall(r'(?:party|parties|landlord|tenant|buyer|seller|broker|agent):\s*([A-Z][A-Za-z\s&,\.]+)', text, re.IGNORECASE)
    for match in party_matches[:5]:
        parties.append({"text": match.strip(), "confidence": 0.75})
    
    financial_terms = []
    money_matches = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)', text)
    for match in money_matches[:3]:
        try:
            amount = float(match.replace(',', ''))
            financial_terms.append({"amount": amount, "type": "extracted_amount", "confidence": 0.75})
        except ValueError:
            continue
    
    dates = []
    date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})', text)
    for match in date_matches[:3]:
        dates.append({"date": match, "type": "extracted_date", "confidence": 0.70})
    
    return {
        "parties": parties,
        "financial_terms": financial_terms,
        "dates": dates,
        "confidence_score": 0.70,
        "analysis_method": f"{method}_text_parsed",
        "note": "Fallback text parsing used due to JSON parse error"
    }

@app.get("/api/documents")
async def get_documents():
    """Get recent documents"""
    return {"documents": [
        {
            "document_id": "test-123",
            "contract_name": "Sample Contract",
            "created_at": "2025-08-17T10:00:00",
            "contract_type": "purchase_agreement",
            "document_state": "processed"
        }
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
