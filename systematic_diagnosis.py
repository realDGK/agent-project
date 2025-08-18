#!/usr/bin/env python3
"""
Systematic Contract Analysis Diagnosis Tool
Traces the complete pipeline from DOCX → Text → AI → Frontend
"""
import requests
import json
from docx import Document
import os

def phase1_systematic_diagnosis():
    """Phase 1: Comprehensive diagnosis of the contract analysis pipeline"""
    
    print("=" * 60)
    print("SYSTEMATIC CONTRACT ANALYSIS DIAGNOSIS")
    print("=" * 60)
    
    # Test file
    test_file = "/home/scott/agent-project/data/samplecontracts/Coyne LOI.docx"
    
    print(f"\n🔍 STEP 1: DOCX Text Extraction")
    print("-" * 40)
    
    # Extract actual text
    try:
        doc = Document(test_file)
        extracted_text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                extracted_text += paragraph.text.strip() + "\n"
        
        print(f"✅ Successfully extracted {len(extracted_text)} characters")
        print(f"📝 First 200 chars: {repr(extracted_text[:200])}")
        
        # Look for key entities that should be found
        key_entities = {
            "Coyne Development": "Coyne Development" in extracted_text,
            "Pegasus Development": "Pegasus Development" in extracted_text,
            "$97,000": "$97,000" in extracted_text,
            "$3,589,000": "$3,589,000" in extracted_text,
            "July 24, 2021": "July 24, 2021" in extracted_text
        }
        
        print(f"\n📊 Key entities in extracted text:")
        for entity, found in key_entities.items():
            status = "✅ FOUND" if found else "❌ MISSING"
            print(f"   {entity}: {status}")
            
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return
    
    print(f"\n🤖 STEP 2: Backend AI Analysis")
    print("-" * 40)
    
    # Test backend API with extracted text
    try:
        response = requests.post('http://localhost:8000/api/analyze-document', 
                               json={
                                   'content': extracted_text,
                                   'filename': 'systematic_test.docx'
                               },
                               timeout=60)
        
        if response.status_code == 200:
            ai_result = response.json()
            metadata = ai_result.get('extracted_metadata', {})
            
            print(f"✅ Backend analysis successful")
            print(f"📊 Analysis method: {metadata.get('analysis_method', 'unknown')}")
            print(f"📊 AI confidence: {metadata.get('confidence_score', 0):.2f}")
            
            # Check what AI found vs what's actually in the document
            ai_parties = metadata.get('parties', [])
            ai_financial = metadata.get('financial_terms', [])
            
            print(f"\n🔍 AI Party Analysis:")
            for i, party in enumerate(ai_parties[:5]):
                party_text = party.get('text', '')[:60]
                conf = party.get('confidence', 0)
                # Check if this party text actually exists in the document
                is_real = party_text.lower() in extracted_text.lower()
                status = "✅ REAL" if is_real else "❌ HALLUCINATION"
                print(f"   {i+1}. {status} - '{party_text}...' (conf: {conf:.2f})")
            
            print(f"\n💰 AI Financial Analysis:")
            for i, term in enumerate(ai_financial[:5]):
                amount = term.get('amount', 0)
                # Check if this amount exists in the document
                amount_formats = [f"${amount:,.0f}", f"${amount:,.2f}", f"{amount:,.0f}"]
                is_real = any(fmt in extracted_text for fmt in amount_formats)
                status = "✅ REAL" if is_real else "❌ HALLUCINATION"
                print(f"   {i+1}. {status} - ${amount:,.2f} (conf: {term.get('confidence', 0):.2f})")
                
        else:
            print(f"❌ Backend analysis failed: {response.status_code}")
            print(f"Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Backend request failed: {e}")
        return
    
    print(f"\n🌐 STEP 3: File Upload API Test")
    print("-" * 40)
    
    # Test the file upload endpoint
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            upload_response = requests.post('http://localhost:8000/api/upload-document', 
                                          files=files, timeout=60)
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            upload_metadata = upload_result.get('extracted_metadata', {})
            
            print(f"✅ File upload analysis successful")
            print(f"📊 Upload confidence: {upload_metadata.get('confidence_score', 0):.2f}")
            
            # Compare upload results vs direct text analysis
            direct_parties = len(ai_result.get('extracted_metadata', {}).get('parties', []))
            upload_parties = len(upload_metadata.get('parties', []))
            
            print(f"\n🔄 Result Comparison:")
            print(f"   Direct text analysis: {direct_parties} parties")
            print(f"   File upload analysis: {upload_parties} parties")
            
            if abs(direct_parties - upload_parties) > 2:
                print(f"⚠️  INCONSISTENCY: Significant difference in results")
            else:
                print(f"✅ CONSISTENT: Similar results from both methods")
                
        else:
            print(f"❌ File upload failed: {upload_response.status_code}")
            
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
    
    print(f"\n📋 STEP 4: Diagnosis Summary")
    print("-" * 40)
    
    # Provide systematic recommendations
    issues_found = []
    recommendations = []
    
    if not all(key_entities.values()):
        issues_found.append("Text extraction missing key entities")
        recommendations.append("Fix DOCX text extraction")
    
    # Check for AI hallucinations
    hallucination_count = 0
    for party in ai_parties[:5]:
        if party.get('text', '').lower() not in extracted_text.lower():
            hallucination_count += 1
    
    if hallucination_count > 2:
        issues_found.append(f"AI hallucinating {hallucination_count}/5 parties")
        recommendations.append("Improve AI prompts to reduce hallucinations")
    
    print(f"🔍 Issues Found: {len(issues_found)}")
    for issue in issues_found:
        print(f"   ❌ {issue}")
    
    print(f"\n💡 Recommendations:")
    for rec in recommendations:
        print(f"   🔧 {rec}")
    
    if not issues_found:
        print("✅ No major issues detected in backend pipeline")
        print("🎯 Focus on frontend display issues")
    
    return ai_result, extracted_text

def phase2_gpt5_integration_plan():
    """Phase 2: Plan for GPT-5 integration"""
    print(f"\n🚀 PHASE 2: GPT-5 INTEGRATION STRATEGY")
    print("-" * 40)
    
    gpt5_advantages = [
        "Superior reasoning for complex contract analysis",
        "Better entity relationship understanding", 
        "More accurate financial term categorization",
        "Reduced hallucination compared to Gemini",
        "Better handling of legal document structure"
    ]
    
    print("🎯 GPT-5 Integration Benefits:")
    for advantage in gpt5_advantages:
        print(f"   ✅ {advantage}")
    
    implementation_steps = [
        "Add OpenAI API integration alongside Gemini",
        "Create GPT-5 specific prompts for contract analysis",
        "Implement three-lane analysis: GPT-5 → Gemini Pro → Human review",
        "Add result comparison and confidence scoring",
        "Fallback chain: GPT-5 fails → Gemini Pro → Gemini Flash"
    ]
    
    print(f"\n🔧 Implementation Steps:")
    for i, step in enumerate(implementation_steps, 1):
        print(f"   {i}. {step}")

if __name__ == "__main__":
    ai_result, extracted_text = phase1_systematic_diagnosis()
    phase2_gpt5_integration_plan()
    
    print(f"\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Fix identified backend issues")
    print("2. Implement GPT-5 integration") 
    print("3. Fix frontend to display real results")
    print("4. End-to-end testing")
    print("=" * 60)