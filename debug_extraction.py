#!/usr/bin/env python3
import requests
from docx import Document
import sys

def extract_actual_text(file_path):
    """Extract actual text from DOCX file"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {e}"

def debug_ai_analysis():
    # Extract actual text from the Coyne LOI
    actual_text = extract_actual_text("/home/scott/agent-project/data/samplecontracts/Coyne LOI.docx")
    
    print("=== ACTUAL DOCUMENT TEXT ===")
    print(f"Length: {len(actual_text)} characters")
    print("Content:")
    print(actual_text[:1000])
    print("...")
    print(actual_text[-500:])
    
    # Now send to AI for analysis
    print("\n=== SENDING TO AI ANALYSIS ===")
    response = requests.post('http://localhost:8000/api/analyze-document', 
                           json={
                               'content': actual_text,
                               'filename': 'debug_coyne_loi.txt'
                           },
                           timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        metadata = result['extracted_metadata']
        
        print(f"AI Analysis Method: {metadata.get('analysis_method', 'unknown')}")
        print(f"AI Confidence: {metadata.get('confidence_score', 0):.2f}")
        
        # Check if AI found parties that actually exist in the text
        parties = metadata.get('parties', [])
        print(f"\n=== PARTY VERIFICATION ===")
        for party in parties[:5]:
            party_text = party.get('text', '')
            if len(party_text) > 10:
                if party_text.lower() in actual_text.lower():
                    print(f"✅ REAL: '{party_text[:50]}...' - FOUND in document")
                else:
                    print(f"❌ FAKE: '{party_text[:50]}...' - NOT in document (HALLUCINATION)")
        
        # Check financial terms
        financial = metadata.get('financial_terms', [])
        print(f"\n=== FINANCIAL TERM VERIFICATION ===")
        for term in financial[:5]:
            amount = term.get('amount', 0)
            amount_str = f"${amount:,.0f}"
            alt_formats = [f"${amount:,.2f}", f"{amount:,.0f}", f"{amount:,.2f}"]
            
            found = any(fmt in actual_text for fmt in alt_formats + [amount_str])
            if found:
                print(f"✅ REAL: {amount_str} - FOUND in document")
            else:
                print(f"❌ FAKE: {amount_str} - NOT in document (HALLUCINATION)")
                
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_ai_analysis()