#!/usr/bin/env python3
"""
Debug script to understand current extraction issues
"""
import sys
import os
sys.path.insert(0, '/home/scott/agent-project')
os.environ["GOOGLE_API_KEY"] = "AIzaSyALGAYh0DRViapjkcGavU6FbijTtwLnfZw"

import json
from docx import Document
import google.generativeai as genai
from simple_extraction import extract_with_gemini_simple, two_stage_extraction

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def test_extraction():
    # Extract text from Coyne LOI
    doc = Document("/home/scott/agent-project/data/samplecontracts/Coyne LOI.docx")
    content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    print("=" * 60)
    print("DEBUG: Current Extraction Pipeline")
    print("=" * 60)
    print(f"Document: Coyne LOI.docx")
    print(f"Content length: {len(content)} chars")
    print(f"First 200 chars: {content[:200]}...")
    
    print("\n" + "=" * 60)
    print("Testing simple_extraction.extract_with_gemini_simple()")
    print("=" * 60)
    
    try:
        result = extract_with_gemini_simple(content, "Coyne LOI.docx")
        
        if result:
            print("✅ Extraction returned something")
            print(f"Result type: {type(result)}")
            print(f"Keys in result: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check what's actually in the result
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, list):
                        print(f"  {key}: {len(value)} items")
                        if value and len(value) > 0:
                            print(f"    First item: {value[0]}")
                    else:
                        print(f"  {key}: {value}")
            
            # Save full result for inspection
            with open('/tmp/extraction_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("\nFull result saved to /tmp/extraction_result.json")
        else:
            print("❌ Extraction returned None/empty")
            
    except Exception as e:
        print(f"❌ Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Testing two_stage_extraction() as fallback")
    print("=" * 60)
    
    try:
        result2 = two_stage_extraction(content, "Coyne LOI.docx")
        if result2:
            print("✅ Two-stage extraction returned something")
            print(f"Keys: {list(result2.keys()) if isinstance(result2, dict) else 'Not a dict'}")
        else:
            print("❌ Two-stage extraction returned None/empty")
    except Exception as e:
        print(f"❌ Two-stage extraction failed: {e}")

if __name__ == "__main__":
    test_extraction()