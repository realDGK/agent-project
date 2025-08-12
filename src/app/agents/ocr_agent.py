#!/usr/bin/env python3
"""
OCR Agent for Scanned PDF Processing
Specialized for real estate contract text extraction
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import tempfile
import hashlib

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    import PyPDF2
except ImportError as e:
    print(f"OCR dependencies not installed: {e}")
    print("Run: pip install pytesseract pdf2image Pillow")

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR processing result"""
    text: str
    confidence: float
    page_count: int
    processing_method: str
    metadata: Dict
    
@dataclass
class DocumentPage:
    """Individual page processing result"""
    page_number: int
    text: str
    confidence: float
    image_path: Optional[str] = None

class OCRAgent:
    """Intelligent OCR agent for real estate documents"""
    
    def __init__(self):
        self.tesseract_config = r'--oem 3 --psm 6'  # Best for dense text documents
        self.dpi = 300  # High quality for legal documents
        
    def extract_text_from_pdf(self, pdf_path: str) -> OCRResult:
        """
        Extract text from PDF using hybrid approach:
        1. Try text extraction first (for digital PDFs)
        2. Fall back to OCR for scanned PDFs
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # First, try direct text extraction
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                digital_text = ""
                
                for page in pdf_reader.pages:
                    digital_text += page.extract_text() + "\n"
                
                # If we got substantial text, it's likely digital
                if len(digital_text.strip()) > 100 and self._has_readable_text(digital_text):
                    logger.info("PDF appears to be digital, using direct text extraction")
                    return OCRResult(
                        text=digital_text.strip(),
                        confidence=0.95,
                        page_count=len(pdf_reader.pages),
                        processing_method="digital_extraction",
                        metadata={
                            "file_size": os.path.getsize(pdf_path),
                            "pages": len(pdf_reader.pages),
                            "extraction_method": "PyPDF2"
                        }
                    )
        except Exception as e:
            logger.warning(f"Digital extraction failed: {e}")
        
        # Fall back to OCR for scanned documents
        logger.info("Using OCR for scanned PDF")
        return self._ocr_pdf_to_text(pdf_path)
    
    def _has_readable_text(self, text: str) -> bool:
        """Check if extracted text appears to be readable (not garbled)"""
        if not text.strip():
            return False
            
        # Check for common legal/contract words
        legal_indicators = [
            'agreement', 'contract', 'party', 'parties', 'whereas',
            'therefore', 'shall', 'property', 'purchase', 'lease',
            'amount', 'date', 'signed', 'executed', 'page'
        ]
        
        text_lower = text.lower()
        indicators_found = sum(1 for indicator in legal_indicators if indicator in text_lower)
        
        # If we find several legal terms, likely readable
        return indicators_found >= 3
    
    def _ocr_pdf_to_text(self, pdf_path: str) -> OCRResult:
        """OCR processing for scanned PDFs"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Convert PDF to images
                logger.info("Converting PDF pages to images...")
                images = convert_from_path(
                    pdf_path, 
                    dpi=self.dpi,
                    output_folder=temp_dir,
                    thread_count=2
                )
                
                pages_processed = []
                total_text = ""
                total_confidence = 0
                
                for i, image in enumerate(images):
                    logger.info(f"Processing page {i+1}/{len(images)}")
                    
                    # OCR the image
                    page_data = pytesseract.image_to_data(
                        image, 
                        config=self.tesseract_config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    page_text = pytesseract.image_to_string(
                        image,
                        config=self.tesseract_config
                    )
                    
                    # Calculate page confidence
                    confidences = [int(conf) for conf in page_data['conf'] if int(conf) > 0]
                    page_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    pages_processed.append(DocumentPage(
                        page_number=i + 1,
                        text=page_text,
                        confidence=page_confidence / 100.0  # Convert to 0-1 range
                    ))
                    
                    total_text += f"\n--- Page {i+1} ---\n{page_text}\n"
                    total_confidence += page_confidence
                
                avg_confidence = (total_confidence / len(images)) / 100.0 if images else 0
                
                return OCRResult(
                    text=total_text.strip(),
                    confidence=avg_confidence,
                    page_count=len(images),
                    processing_method="tesseract_ocr",
                    metadata={
                        "file_size": os.path.getsize(pdf_path),
                        "dpi": self.dpi,
                        "tesseract_config": self.tesseract_config,
                        "pages_processed": len(pages_processed),
                        "avg_page_confidence": avg_confidence
                    }
                )
                
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                return OCRResult(
                    text="",
                    confidence=0.0,
                    page_count=0,
                    processing_method="failed",
                    metadata={"error": str(e)}
                )

    def process_document(self, file_path: str) -> OCRResult:
        """Main entry point for document processing"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

# Convenience function for quick testing
def quick_ocr_test(pdf_path: str) -> None:
    """Quick test of OCR functionality"""
    agent = OCRAgent()
    result = agent.process_document(pdf_path)
    
    print(f"\n📄 OCR Results for {os.path.basename(pdf_path)}:")
    print(f"Method: {result.processing_method}")
    print(f"Pages: {result.page_count}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Text length: {len(result.text)} characters")
    print(f"First 200 chars: {result.text[:200]}...")

if __name__ == "__main__":
    # Test with a sample contract
    sample_pdf = "/home/scott/agent-project/data/samplecontracts/Clevenger Release of Ponds.pdf"
    if os.path.exists(sample_pdf):
        quick_ocr_test(sample_pdf)
    else:
        print("Sample PDF not found for testing")