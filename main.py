"""
Simplified FastAPI backend - clean extraction with AI only
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import uuid
import re
import hashlib

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import google.generativeai as genai
from persist_extraction import persist_extraction, build_db_extraction_payload
from provenance_persist import persist_with_provenance, create_review_task_if_needed
from db_selftest import router as db_selftest_router
from simple_extraction import (
    extract_with_gemini_simple,
    two_stage_extraction
)
from precision_extraction import (
    extract_with_precision,
    extract_with_enhanced_precision
)
from enhanced_extraction import extract_with_slug_schema

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Contract Analysis Backend", version="2.0.0")
app.include_router(db_selftest_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    extracted_metadata: Dict[str, Any]  # Frontend expects this field name
    requires_human_review: bool
    analysis_timestamp: str
    document_text: Optional[str] = None

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
    """Serve the main upload UI"""
    if os.path.exists("web-interface.html"):
        return FileResponse("web-interface.html", media_type="text/html")
    else:
        return HTMLResponse(content="<h1>Contract Analysis System</h1><p>Upload interface not found.</p>", status_code=404)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file formats"""
    try:
        if filename.lower().endswith('.docx'):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(file_content))
                text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
                return text.strip()
            except ImportError:
                logger.warning("python-docx not available")
                # Try simple text extraction
                text_content = file_content.decode('utf-8', errors='ignore')
                # Remove obvious XML/binary artifacts
                text_content = re.sub(r'<[^>]+>', ' ', text_content)
                text_content = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', text_content)
                text_content = re.sub(r'\s+', ' ', text_content)
                return text_content.strip()
        elif filename.lower().endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')
        elif filename.lower().endswith('.pdf'):
            logger.warning("PDF processing not yet implemented")
            return "PDF processing not yet implemented"
        else:
            return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}")
        return f"Error extracting text: {str(e)}"

def clean_content(content: str) -> str:
    """Clean up noisy content"""
    if len(content) > 50000 and ('<?xml' in content or 'word/' in content):
        logger.info("Detected noisy content, cleaning")
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'[^\x20-\x7E\n\r\t]', ' ', content)
        content = re.sub(r'\s+', ' ', content)
    return content.strip()

@app.post("/api/upload-document", response_model=DocumentAnalysisResult)
async def upload_document(file: UploadFile = File(...)):
    """Upload and analyze a document"""
    try:
        file_content = await file.read()
        extracted_text = extract_text_from_file(file_content, file.filename)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        logger.info(f"Extracted {len(extracted_text)} characters from {file.filename}")
        
        request = DocumentAnalysisRequest(
            content=extracted_text,
            filename=file.filename
        )
        
        return await analyze_document(request)
        
    except Exception as e:
        logger.exception("File upload failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-document", response_model=DocumentAnalysisResult)
async def analyze_document(request: DocumentAnalysisRequest):
    """Analyze document with AI extraction only"""
    try:
        start_time = datetime.now()
        
        # Clean content
        cleaned_content = clean_content(request.content)
        
        # Create document ID
        pool = await get_db_pool()
        doc_id = str(uuid.uuid4())
        
        # AI Analysis
        extracted_data = {}
        confidence_score = 0.0
        
        if GOOGLE_API_KEY:
            # Try enhanced extraction with slug-based schemas first
            ai_result = extract_with_slug_schema(cleaned_content, request.filename)
            
            if ai_result and not ai_result.get('error'):
                # Data is already in standard format from enhanced extraction
                extracted_data = ai_result
                confidence_score = ai_result.get('confidence_score', 0.95)
                contract_slug = ai_result.get('contract_slug', 'unknown')
                logger.info(f"Enhanced extraction successful for {doc_id}")
                logger.info(f"Contract type: {ai_result.get('document_type', {}).get('type', 'unknown')} (slug: {contract_slug})")
                logger.info(f"Extracted: {len(ai_result.get('parties', []))} parties, {len(ai_result.get('financial_terms', []))} financial terms, {len(ai_result.get('dates', []))} dates")
            else:
                # Fallback to precision extraction
                logger.info("Enhanced extraction failed, trying precision extraction")
                ai_result = extract_with_enhanced_precision(cleaned_content, request.filename)
                
                if ai_result and not ai_result.get('error'):
                    extracted_data = {
                        'parties': ai_result.get('parties', []),
                        'financial_terms': ai_result.get('financials', ai_result.get('financial_terms', [])),
                        'dates': ai_result.get('dates_and_periods', ai_result.get('dates', [])),
                        'property_details': ai_result.get('property_details', {}),
                        'document_type': ai_result.get('document_details', {})
                    }
                    confidence_score = ai_result.get('confidence_score', 0.85)
                    logger.info(f"Simple extraction successful for {doc_id}")
                else:
                    logger.error(f"All extraction methods failed for {doc_id}")
                    extracted_data = {"extraction_failed": True, "reason": "AI extraction failed"}
        else:
            extracted_data = {"extraction_failed": True, "reason": "No API key configured"}
        
        # Persist to database if extraction succeeded
        if extracted_data and not extracted_data.get('extraction_failed'):
            try:
                # Use new provenance-aware persistence
                success = await persist_with_provenance(
                    pool, doc_id, request.filename, 
                    cleaned_content, extracted_data, confidence_score
                )
                
                if success:
                    logger.info(f"Persisted extraction with provenance for document {doc_id}")
                    logger.info(f"Stored: {len(extracted_data.get('parties', []))} parties, {len(extracted_data.get('financial_terms', []))} financial terms")
                    
                    # Create review task if needed
                    await create_review_task_if_needed(
                        pool, doc_id, 
                        hashlib.sha256(cleaned_content.encode()).hexdigest(),
                        confidence_score, extracted_data
                    )
                else:
                    logger.error(f"Failed to persist extraction for {doc_id}")
            except Exception as e:
                logger.error(f"Failed to persist: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DocumentAnalysisResult(
            document_id=doc_id,
            filename=request.filename,
            processing_time=processing_time,
            confidence_score=confidence_score,
            extracted_metadata=extracted_data,  # Map to frontend expected field name
            requires_human_review=confidence_score < 0.8,
            analysis_timestamp=datetime.now().isoformat(),
            document_text=cleaned_content if len(cleaned_content) < 50000 else None
        )
        
    except Exception as e:
        logger.exception("Document analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

def determine_contract_type(filename: str, extracted_data: dict) -> str:
    """Determine contract type from filename and extracted data"""
    # First try from AI extraction
    if 'document_type' in extracted_data:
        doc_type = extracted_data['document_type']
        if isinstance(doc_type, dict):
            return doc_type.get('type', 'Unknown')
        elif isinstance(doc_type, str):
            return doc_type
    
    # Fallback to filename analysis
    filename_lower = filename.lower()
    if 'loi' in filename_lower or 'letter of intent' in filename_lower:
        return "Letter of Intent"
    elif 'lease' in filename_lower:
        return "Lease Agreement"
    elif 'purchase' in filename_lower or 'psa' in filename_lower:
        return "Purchase Agreement"
    elif 'nda' in filename_lower:
        return "NDA"
    elif 'amendment' in filename_lower:
        return "Amendment"
    
    return "Unknown"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
