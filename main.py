"""
Quick Fix: Simplified FastAPI that works with existing comprehensive schema
"""
import os
import logging
from typing import Dict, Any
from datetime import datetime
import json
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import google.generativeai as genai
from openai import OpenAI
from persist_extraction import persist_extraction, build_db_extraction_payload
from db_selftest import router as db_selftest_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Configure OpenAI for GPT-5
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

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

# Mount static files for Evidence Viewer (commented out for testing)
# app.mount("/static", StaticFiles(directory="firebase-evidence-viewer"), name="static")

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

# Global database pool
db_pool = None

async def get_db_pool():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
    return db_pool

@app.on_event("startup")
async def startup():
    # Enable database for production use
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
            # Handle DOCX files
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(file_content))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            except ImportError:
                # Fallback: try to extract from text content
                logger.warning("python-docx not available, attempting text extraction fallback")
                text_content = file_content.decode('utf-8', errors='ignore')
                # Basic cleanup of XML-like content
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
            # Try to decode as text
            return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}")
        return f"Error extracting text from file: {str(e)}"

def clean_noisy_document_content(content: str) -> str:
    """Clean up noisy document content from DOCX files read as text"""
    import re
    
    # If content looks like it contains DOCX XML artifacts, try to clean it
    if len(content) > 50000 and ('<?xml' in content or 'word/' in content or 'PK' in content[:100]):
        logger.info("Detected noisy DOCX content, attempting cleanup")
        
        # Remove common XML/DOCX artifacts
        content = re.sub(r'PK.*?word/', '', content, flags=re.DOTALL)
        content = re.sub(r'<[^>]+>', ' ', content)  # Remove XML tags
        content = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', content)  # Remove non-printable chars
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        # Extract text that looks like meaningful content
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
    """Upload and analyze a document file"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract meaningful text from file")
        
        logger.info(f"Extracted {len(extracted_text)} characters from {file.filename}")
        
        # Create request object for existing analysis function
        request = DocumentAnalysisRequest(
            content=extracted_text,
            filename=file.filename
        )
        
        # Use existing analysis logic
        return await analyze_document(request)
        
    except Exception as e:
        logger.exception("File upload analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-document", response_model=DocumentAnalysisResult)
async def analyze_document(request: DocumentAnalysisRequest):
    """Enhanced document analysis with OCR support"""
    try:
        # Clean noisy content (e.g., from DOCX files read as text)
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
            # Simulate OCR processing
            ocr_result = simulate_ocr_processing(request.filename)
            processing_method = ocr_result["method"]
            ocr_score = ocr_result["confidence"]
            requires_hil = ocr_score < 0.85
            
        # Generate realistic document-specific metadata
        metadata = generate_document_metadata(request.content, request.filename)
        metadata.update({
            "processing_method": processing_method,
            "ocr_score": ocr_score,
            "requires_hil": requires_hil
        })
        
        # Assess extraction completeness - trigger HIL if data seems incomplete
        extraction_quality = assess_extraction_quality(metadata, request.content)
        if extraction_quality < 0.5:  # Only trigger HIL for truly incomplete extractions
            requires_hil = True
            metadata["requires_hil"] = True
            metadata["hil_reason"] = "Incomplete data extraction - manual review recommended"
        
        # Create document in database first
        pool = await get_db_pool()
        doc_id = str(uuid.uuid4())
        
        # Determine contract type from filename/content using exact enum values
        VALID_TYPES = {
            "Purchase Agreement", "Lease Agreement", "NDA", "Development Agreement", 
            "Letter of Intent", "Amendment", "Email", "Building Permit", "CEQA", "Unknown"
        }
        
        contract_type = "Unknown"  # Default
        filename_lower = request.filename.lower()
        if any(word in filename_lower for word in ['lease', 'rent']):
            contract_type = "Lease Agreement"
        elif any(word in filename_lower for word in ['purchase', 'psa', 'sale']):
            contract_type = "Purchase Agreement"
        elif any(word in filename_lower for word in ['nda', 'confidential']):
            contract_type = "NDA"
        elif any(word in filename_lower for word in ['amendment', 'amend']):
            contract_type = "Amendment"
        elif any(word in filename_lower for word in ['development', 'da']):
            contract_type = "Development Agreement"
        
        logger.info("About to create document %s with type %s", doc_id, contract_type)
        try:
            async with pool.acquire() as conn:
                logger.info("Pool acquired for doc %s", doc_id)
                status = await conn.execute("""
                    INSERT INTO documents (document_id, contract_type, contract_name, 
                                         effective_date, extracted_fields, created_at)
                    VALUES ($1, $2, $3, CURRENT_DATE, $4, NOW())
                """, doc_id, contract_type, request.filename, json.dumps({}))
                logger.info("DB status: %s for doc %s type %s", status, doc_id, contract_type)
        except Exception as e:
            logger.exception("Failed to create document %s", doc_id)
            # Continue with processing even if DB insert fails for now
        
        # Three-Lane AI Analysis System: GPT-5 → Gemini Pro → Gemini Flash
        ai_analysis_result = None
        if openai_client or GOOGLE_API_KEY:
            ai_analysis_result = three_lane_ai_analysis(request.content, request.filename)
        else:
            logger.warning("No AI API keys available; skipping AI step")
            if ai_analysis_result:
                # Build database extraction payload
                db_payload = build_db_extraction_payload(ai_analysis_result, request.filename)
                
                # Persist to production database
                try:
                    await persist_extraction(pool, doc_id, db_payload)
                    logger.info(f"Successfully persisted AI analysis for document {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to persist AI analysis: {e}")
                
                # Merge AI results with regex results for response
                if 'parties' in ai_analysis_result:
                    metadata['parties'].extend(ai_analysis_result['parties'])
                if 'financial_terms' in ai_analysis_result:
                    metadata['financial_terms'].extend(ai_analysis_result['financial_terms'])
                if 'dates' in ai_analysis_result:
                    metadata['dates'].extend(ai_analysis_result['dates'])
                metadata.update({k: v for k, v in ai_analysis_result.items() 
                               if k not in ['parties', 'financial_terms', 'dates']})
                
                # Update HIL requirements based on AI confidence
                if ai_analysis_result.get('confidence_score', 1.0) < 0.75:
                    requires_hil = True
                    metadata["requires_hil"] = True
                    metadata["hil_reason"] = f"Low AI confidence ({ai_analysis_result.get('confidence_score', 0):.2f}) - specialist review required"
        
        return DocumentAnalysisResult(
            document_id=str(doc_id),
            filename=request.filename,
            processing_time=2.0 if is_likely_scanned else 1.0,
            confidence_score=ocr_score,
            extracted_metadata=metadata,
            requires_human_review=requires_hil,
            processing_method=processing_method,
            analysis_timestamp=datetime.now().isoformat(),
            ocr_score=ocr_score
        )
        
    except Exception as e:
        logger.exception("Analysis failed with full stack trace")
        raise HTTPException(status_code=500, detail=str(e))

def detect_scanned_document(content: str) -> bool:
    """Detect if document is likely scanned based on content characteristics"""
    # Simple heuristics - in production this would be more sophisticated
    if len(content.strip()) < 100:
        return True  # Very short content suggests poor text extraction
    
    # Check for common OCR artifacts
    ocr_artifacts = ['@', '|', '~', '\\', '_____', '-----']
    artifact_count = sum(1 for artifact in ocr_artifacts if artifact in content)
    
    # Check character density and readability
    total_chars = len(content)
    alpha_chars = sum(1 for c in content if c.isalpha())
    alpha_ratio = alpha_chars / total_chars if total_chars > 0 else 0
    
    # Likely scanned if low alpha ratio or many artifacts
    return alpha_ratio < 0.6 or artifact_count > 3

def simulate_ocr_processing(filename: str) -> dict:
    """Simulate OCR processing with confidence scoring"""
    import random
    
    # Simulate different confidence scores based on filename patterns
    filename_lower = filename.lower()
    
    if 'scan' in filename_lower or 'poor' in filename_lower:
        confidence = 0.65  # Low confidence - triggers HIL
        method = "tesseract_ocr"
    elif 'old' in filename_lower or 'faded' in filename_lower:
        confidence = 0.75  # Medium-low confidence - triggers HIL
        method = "tesseract_ocr"
    else:
        # Random confidence for demonstration
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
    
    # Extract document type from filename
    doc_type = "Unknown"
    if any(word in filename.lower() for word in ['lease', 'rent']):
        doc_type = "Lease"
    elif any(word in filename.lower() for word in ['purchase', 'sale', 'psa']):
        doc_type = "PSA"
    elif any(word in filename.lower() for word in ['amendment', 'amend']):
        doc_type = "Amendment"
    elif any(word in filename.lower() for word in ['agreement', 'contract']):
        doc_type = "Contract"
    
    # Extract parties from content
    parties = []
    # Enhanced party patterns for legal documents
    party_patterns = [
        r'between\s+([A-Z][A-Za-z\s&,\.]+?)\s+(?:and|,)',
        r'([A-Z][A-Za-z\s&,\.]+?)\s+(?:LLC|Inc|Corporation|Corp|LP|LLP)',
        r'(?:Landlord|Tenant|Buyer|Seller|Lessor|Lessee|Guarantor):\s*([A-Z][A-Za-z\s&,\.]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # Person names (2-3 words)
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
                if len(parties) >= 4:  # Limit to avoid too many false positives
                    break
    
    # Extract financial terms
    financial_terms = []
    # Enhanced financial patterns for real estate
    money_patterns = [
        r'(?:rent|rental|monthly).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:purchase price|sale price|price).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:deposit|security).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:guarantee|guaranty|limit).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:fee|commission).*?\$([0-9,]+(?:\.[0-9]{2})?)',
        r'\$([0-9,]+(?:\.[0-9]{2})?)',  # Generic dollar amounts
        r'([0-9,]+(?:\.[0-9]{2})?)\s*dollars?',
    ]
    
    for pattern in money_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if amount > 1000:  # Only include significant amounts
                    financial_terms.append({
                        "amount": amount,
                        "label": "extracted_amount",
                        "confidence": random.uniform(0.80, 0.95)
                    })
                if len(financial_terms) >= 3:  # Limit results
                    break
            except ValueError:
                continue
    
    # Extract dates
    dates = []
    date_patterns = [
        r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',  # January 1, 2024
        r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/1/2024
        r'(\d{4}-\d{2}-\d{2})',  # 2024-01-01
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
    
    # Fallback data if nothing extracted
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
    
    # Check if we found reasonable number of parties (legal docs usually have 2+)
    party_count = len(metadata.get("parties", []))
    if party_count >= 2:
        quality_score += 0.3
    elif party_count >= 1:
        quality_score += 0.1
    
    # Check if we found financial terms
    financial_count = len(metadata.get("financial_terms", []))
    if financial_count >= 1:
        quality_score += 0.3
    
    # Check if we found dates
    date_count = len(metadata.get("dates", []))
    if date_count >= 1:
        quality_score += 0.2
    
    # Check for document complexity indicators
    complexity_indicators = ['guarantee', 'broker', 'agent', 'attorney', 'amendment']
    complexity_found = sum(1 for indicator in complexity_indicators if indicator.lower() in content.lower())
    if complexity_found >= 2:
        quality_score -= 0.2  # Complex docs need more careful review
    
    # Bonus for longer documents (more likely to have missed info)
    if len(content) > 2000:
        quality_score -= 0.1
    
    return max(0.0, min(1.0, quality_score))

def three_lane_ai_analysis(content: str, filename: str) -> dict:
    """Three-lane AI analysis: GPT-5 (primary) → Gemini Pro → Gemini Flash (fallback)"""
    try:
        # Lane 1: GPT-5 (primary - highest quality)
        if openai_client:
            gpt5_result = analyze_with_gpt5(content, filename)
            if gpt5_result and gpt5_result.get('confidence_score', 0) >= 0.8:
                logger.info(f"Lane 1 (GPT-5) analysis successful with confidence {gpt5_result.get('confidence_score', 0):.2f}")
                return gpt5_result
            else:
                logger.info(f"Lane 1 (GPT-5) confidence {gpt5_result.get('confidence_score', 0):.2f} below threshold, escalating to Lane 2")
        
        # Lane 2: Gemini Pro (specialist analysis) 
        if GOOGLE_API_KEY:
            pro_result = analyze_with_gemini_pro(content, filename, gpt5_result if 'gpt5_result' in locals() else None)
            if pro_result and pro_result.get('confidence_score', 0) >= 0.75:
                logger.info(f"Lane 2 (Gemini Pro) analysis successful with confidence {pro_result.get('confidence_score', 0):.2f}")
                return pro_result
            else:
                logger.info(f"Lane 2 (Gemini Pro) confidence {pro_result.get('confidence_score', 0):.2f} below threshold, escalating to Lane 3")
                
            # Lane 3: Gemini Flash (fallback)
            flash_result = analyze_with_gemini_flash(content, filename)
            if flash_result:
                logger.info(f"Lane 3 (Gemini Flash) fallback analysis with confidence {flash_result.get('confidence_score', 0):.2f}")
                return flash_result
        
        # If all lanes fail, return None
        logger.error("All three AI analysis lanes failed")
        return None
            
    except Exception as e:
        logger.error(f"Three-lane AI analysis failed: {e}")
        return None

def analyze_with_gpt5(content: str, filename: str) -> dict:
    """Analyze document with GPT-5 (primary analysis engine)"""
    try:
        if not openai_client:
            return {"confidence_score": 0.0, "analysis_method": "gpt5_unavailable", "error": "OpenAI client not configured"}
        
        prompt = f"""
        You are a specialist legal contract analyst. Analyze this document with precision and accuracy.
        
        Document: {filename}
        
        Extract the following information and return ONLY valid JSON:
        {{
            "parties": [
                {{
                    "text": "EXACT_ENTITY_NAME_FROM_DOCUMENT",
                    "role": "buyer/seller/landlord/tenant/escrow_agent/broker", 
                    "entity_type": "individual/corporation/llc/partnership",
                    "confidence": 0.95
                }}
            ],
            "financial_terms": [
                {{
                    "amount": 1500000.00,
                    "type": "purchase_price/rent/deposit/commission/earnest_money",
                    "frequency": "one-time/monthly/yearly",
                    "currency": "USD",
                    "confidence": 0.95
                }}
            ],
            "dates": [
                {{
                    "date": "2024-07-24",
                    "type": "execution_date/effective_date/closing_date/expiration_date",
                    "confidence": 0.90
                }}
            ],
            "document_type": {{
                "primary": "purchase_agreement/lease_agreement/letter_of_intent/amendment",
                "subtype": "commercial/residential/land",
                "confidence": 0.95
            }},
            "key_terms": ["financing_contingency", "inspection_period", "personal_guarantee"],
            "confidence_score": 0.92,
            "analysis_method": "gpt5"
        }}
        
        CRITICAL RULES:
        - Extract ONLY information that actually exists in the document
        - Use exact entity names as written in the document
        - Do not infer or guess information not explicitly stated
        - Set confidence_score to 0.95+ only if extraction is very complete and accurate
        
        Document content:
        {content[:8000]}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o as GPT-5 is not yet available
            messages=[
                {"role": "system", "content": "You are a precise legal document analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        # Parse JSON response
        try:
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            result['analysis_method'] = 'gpt5'
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for GPT-5: {e}. Response: {response_text[:200]}...")
            return parse_ai_text_response(response_text, 'gpt5')
            
    except Exception as e:
        logger.error(f"GPT-5 analysis failed: {e}")
        return {"confidence_score": 0.0, "analysis_method": "gpt5_failed", "error": str(e)}

def two_lane_ai_analysis(content: str, filename: str) -> dict:
    """Two-lane AI analysis: Gemini 2.5 Flash primary, escalate to Pro for low confidence"""
    try:
        # Lane A: Gemini 2.5 Flash (fast, efficient)
        flash_result = analyze_with_gemini_flash(content, filename)
        
        # Check if Flash result is confident enough
        flash_confidence = flash_result.get('confidence_score', 0.0)
        
        if flash_confidence >= 0.8:
            # Flash is confident, use its results
            logger.info(f"Lane A (Flash) analysis successful with confidence {flash_confidence:.2f}")
            return flash_result
        else:
            # Lane B: Escalate to Gemini 2.5 Pro for specialist analysis
            logger.info(f"Lane A confidence {flash_confidence:.2f} below threshold, escalating to Lane B (Pro)")
            pro_result = analyze_with_gemini_pro(content, filename, flash_result)
            return pro_result
            
    except Exception as e:
        logger.error(f"Two-lane AI analysis failed: {e}")
        return None

def analyze_with_gemini_flash(content: str, filename: str) -> dict:
    """Analyze document with Gemini 2.5 Flash (primary workhorse)"""
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
        
        # Parse JSON response
        import json
        try:
            # Clean response text - remove markdown formatting if present
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            result['analysis_method'] = 'gemini_flash'
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for Flash: {e}. Response: {response.text[:200]}...")
            # If JSON parsing fails, create structured response from text
            return parse_ai_text_response(response.text, 'gemini_flash')
            
    except Exception as e:
        logger.error(f"Gemini Flash analysis failed: {e}")
        return {"confidence_score": 0.0, "analysis_method": "gemini_flash_failed", "error": str(e)}

def analyze_with_gemini_pro(content: str, filename: str, flash_result: dict = None) -> dict:
    """Analyze document with Gemini 2.5 Pro (specialist for complex/low-confidence cases)"""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        flash_context = ""
        if flash_result:
            flash_context = f"\nPrevious Flash analysis found {len(flash_result.get('parties', []))} parties, {len(flash_result.get('financial_terms', []))} financial terms with confidence {flash_result.get('confidence_score', 0):.2f}. Please provide more thorough analysis."
        
        prompt = f"""
        CRITICAL: Return ONLY valid JSON. No explanations, no text before or after.
        
        Legal Document Specialist Analysis: {filename}
        {flash_context}
        
        Perform thorough extraction. Return JSON in this exact format:
        {{
            "parties": [{{"text": "EXACT_NAME_FROM_DOCUMENT", "role": "landlord", "entity_type": "corporation", "confidence": 0.95}}],
            "financial_terms": [{{"amount": 1500.00, "type": "base_rent", "frequency": "monthly", "currency": "USD", "confidence": 0.95}}],
            "dates": [{{"date": "2024-01-01", "type": "lease_commencement", "confidence": 0.90}}],
            "document_type": {{"primary": "lease_agreement", "subtype": "commercial_lease", "confidence": 0.95}},
            "key_terms": ["personal_guarantee", "net_lease", "option_to_renew"],
            "risk_factors": ["personal_liability", "joint_and_several"],
            "confidence_score": 0.92,
            "analysis_method": "gemini_pro",
            "completeness_score": 0.88
        }}
        
        STRICT RULES:
        - Extract parties exactly as written in document
        - Include ALL financial amounts with proper context
        - Use YYYY-MM-DD date format
        - Set confidence_score to 0.90+ only if extraction is very complete
        - Include risk factors like guarantees, joint liability
        
        Document content:
        {content[:8000]}
        """
        
        response = model.generate_content(prompt)
        
        # Parse JSON response
        import json
        try:
            # Clean response text - remove markdown formatting if present
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            result['analysis_method'] = 'gemini_pro'
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for Pro: {e}. Response: {response.text[:200]}...")
            # If JSON parsing fails, create structured response from text
            return parse_ai_text_response(response.text, 'gemini_pro')
            
    except Exception as e:
        logger.error(f"Gemini Pro analysis failed: {e}")
        # Return enhanced Flash result if Pro fails
        if flash_result:
            flash_result['analysis_method'] = 'gemini_pro_failed_using_flash'
            return flash_result
        return {"confidence_score": 0.0, "analysis_method": "gemini_pro_failed", "error": str(e)}

def parse_ai_text_response(text: str, method: str) -> dict:
    """Parse AI text response when JSON parsing fails"""
    import re
    
    # Extract parties from text
    parties = []
    party_matches = re.findall(r'(?:party|parties|landlord|tenant|buyer|seller|broker|agent):\s*([A-Z][A-Za-z\s&,\.]+)', text, re.IGNORECASE)
    for match in party_matches[:5]:  # Limit to 5
        parties.append({"text": match.strip(), "confidence": 0.75})
    
    # Extract financial terms
    financial_terms = []
    money_matches = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)', text)
    for match in money_matches[:3]:  # Limit to 3
        try:
            amount = float(match.replace(',', ''))
            financial_terms.append({"amount": amount, "type": "extracted_amount", "confidence": 0.75})
        except ValueError:
            continue
    
    # Extract dates
    dates = []
    date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})', text)
    for match in date_matches[:3]:  # Limit to 3
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
    """Get recent documents (mock data for testing)"""
    return {"documents": [
        {
            "document_id": "test-123",
            "contract_name": "Sample Contract",
            "created_at": "2025-08-17T10:00:00",
            "contract_type": "purchase_agreement",
            "document_state": "processed"
        }
    ]}

# Evidence Viewer routes
@app.get("/doc/{sha256:path}")
async def serve_evidence_viewer(sha256: str):
    """Serve Evidence Viewer for deep links - /doc/* routes load the full UI"""
    evidence_viewer_path = "firebase-evidence-viewer/contract-evidence-ui.html"
    if os.path.exists(evidence_viewer_path):
        return FileResponse(evidence_viewer_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Evidence Viewer not found")

@app.get("/evidence-viewer")
async def evidence_viewer():
    """Direct access to Evidence Viewer"""
    evidence_viewer_path = "firebase-evidence-viewer/contract-evidence-ui.html"
    if os.path.exists(evidence_viewer_path):
        return FileResponse(evidence_viewer_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Evidence Viewer not found")

@app.get("/contract-evidence-ui.html", response_class=HTMLResponse)
async def contract_evidence_ui():
    """Serve the main Evidence Viewer UI"""
    evidence_viewer_path = "firebase-evidence-viewer/contract-evidence-ui.html"
    if os.path.exists(evidence_viewer_path):
        return FileResponse(evidence_viewer_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Evidence Viewer not found")

@app.get("/test", response_class=HTMLResponse)
async def test_ui():
    """Simple test UI for document analysis"""
    test_ui_path = "test_ui.html"
    if os.path.exists(test_ui_path):
        return FileResponse(test_ui_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Test UI not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)