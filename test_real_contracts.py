#!/usr/bin/env python3
import requests
import json
import os
from docx import Document

def extract_docx_text(file_path):
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return None

def test_contract_analysis(file_path, filename):
    """Test contract analysis with real file"""
    print(f"\n=== Testing {filename} ===")
    
    # Extract text content
    if file_path.endswith('.docx'):
        content = extract_docx_text(file_path)
    else:
        print(f"Skipping {filename} - unsupported format for now")
        return
    
    if not content:
        print(f"Failed to extract content from {filename}")
        return
    
    print(f"Extracted {len(content)} characters")
    print(f"First 200 chars: {content[:200]}...")
    
    # Send to analysis API
    try:
        response = requests.post('http://localhost:8000/api/analyze-document', 
                               json={
                                   'content': content,
                                   'filename': filename
                               },
                               timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis successful!")
            print(f"Document ID: {result['document_id']}")
            print(f"Confidence: {result['confidence_score']}")
            print(f"HIL Required: {result['requires_human_review']}")
            print(f"Processing Method: {result['processing_method']}")
            
            metadata = result['extracted_metadata']
            print(f"Analysis Method: {metadata.get('analysis_method', 'unknown')}")
            
            # Check parties
            parties = metadata.get('parties', [])
            print(f"Parties found: {len(parties)}")
            for i, party in enumerate(parties[:3]):  # Show first 3
                print(f"  {i+1}. {party.get('text', '')[:50]}... (conf: {party.get('confidence', 0):.2f})")
            
            # Check financial terms
            financial = metadata.get('financial_terms', [])
            print(f"Financial terms: {len(financial)}")
            for i, term in enumerate(financial[:3]):  # Show first 3
                amount = term.get('amount', 0)
                term_type = term.get('type', term.get('label', 'unknown'))
                conf = term.get('confidence', 0)
                print(f"  {i+1}. ${amount:,.2f} ({term_type}) (conf: {conf:.2f})")
            
            # Check dates
            dates = metadata.get('dates', [])
            print(f"Dates found: {len(dates)}")
            for i, date in enumerate(dates[:3]):  # Show first 3
                date_text = date.get('date', date.get('text', ''))
                date_type = date.get('type', date.get('label', 'unknown'))
                conf = date.get('confidence', 0)
                print(f"  {i+1}. {date_text} ({date_type}) (conf: {conf:.2f})")
            
            if result['requires_human_review']:
                hil_reason = metadata.get('hil_reason', 'Unknown reason')
                print(f"🔍 HIL Reason: {hil_reason}")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    # Test with real contracts
    contracts_dir = "/home/scott/agent-project/data/samplecontracts"
    
    # Test DOCX files first
    docx_files = [
        "PURCHASE AND SALE AGREEMENT AND ESCROW INSTRUCTIONS.docx",
        "Schussing_PURCHASE AND SALE AGREEMENT AND ESCROW INSTRUCTIONS.docx", 
        "SECOND AMENDMENT TO DEVELOPMENT AGREEMENT.docx",
        "Coyne LOI.docx"
    ]
    
    for filename in docx_files:
        file_path = os.path.join(contracts_dir, filename)
        if os.path.exists(file_path):
            test_contract_analysis(file_path, filename)
        else:
            print(f"File not found: {filename}")