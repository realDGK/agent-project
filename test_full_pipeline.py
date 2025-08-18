#!/usr/bin/env python3
"""
Test the full OCR + AI + Database pipeline
"""
import requests
import json

def test_document_processing():
    """Test the complete document processing pipeline"""
    
    # Sample document content (lease agreement)
    sample_content = """
    COMMERCIAL LEASE AGREEMENT
    
    This Lease Agreement is made between ABC Properties LLC (Landlord) 
    and Tech Startup Inc (Tenant) for the premises located at 
    123 Main Street, Suite 400, San Francisco, CA.
    
    MONTHLY RENT: $15,000 per month
    LEASE TERM: 24 months commencing January 1, 2025
    SECURITY DEPOSIT: $30,000 due upon execution
    
    TENANT OBLIGATIONS:
    1. Pay monthly rent by the 1st of each month
    2. Maintain property insurance with minimum $1M coverage
    3. Provide 30 days written notice before lease termination
    
    Executed on December 15, 2024
    """
    
    # Test the document analysis endpoint
    payload = {
        "content": sample_content,
        "filename": "commercial_lease_downtown.pdf",
        "options": {
            "useLegalBERT": True,
            "trackLifecycle": True,
            "extractEntities": True
        }
    }
    
    print("🚀 Testing document processing pipeline...")
    print(f"📄 Document: {payload['filename']}")
    print(f"📝 Content length: {len(sample_content)} characters")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/analyze-document",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ Document processed successfully!")
            print(f"🆔 Document ID: {result['document_id']}")
            print(f"⏱️  Processing time: {result['processing_time']}s") 
            print(f"🎯 Confidence score: {result['confidence_score']}")
            print(f"🔧 Processing method: {result['processing_method']}")
            print(f"👥 HIL required: {result['requires_human_review']}")
            
            # Show extracted metadata
            metadata = result['extracted_metadata']
            print(f"\n📊 Extracted metadata:")
            print(f"   - Parties: {len(metadata.get('parties', []))}")
            print(f"   - Financial terms: {len(metadata.get('financial_terms', []))}")
            print(f"   - Dates: {len(metadata.get('dates', []))}")
            
            # Check if AI analysis was performed
            if 'analysis_method' in metadata:
                print(f"   - AI Analysis: {metadata['analysis_method']}")
                
            return result
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return None

def verify_database_storage(doc_id):
    """Check if the document was properly stored in the database"""
    import asyncpg
    import asyncio
    
    async def check_db():
        conn = await asyncpg.connect(
            "postgresql://agent_user:agent_password@localhost:5432/agent_orchestration"
        )
        
        try:
            # Check document
            doc = await conn.fetchrow(
                "SELECT contract_name, extracted_fields FROM documents WHERE document_id = $1",
                doc_id
            )
            
            if doc:
                print(f"\n🗄️  Database verification:")
                print(f"   - Document found: {doc['contract_name']}")
                print(f"   - Extracted fields: {len(doc['extracted_fields'])} keys")
                
                # Check obligations
                obligations = await conn.fetch(
                    "SELECT obligation_type, description, status FROM obligations WHERE document_id = $1",
                    doc_id
                )
                
                print(f"   - Obligations stored: {len(obligations)}")
                for i, ob in enumerate(obligations, 1):
                    print(f"     {i}. {ob['obligation_type']}: {ob['description']} ({ob['status']})")
                    
                # Check evidence
                evidence_count = await conn.fetchval(
                    """SELECT COUNT(*) FROM obligation_evidence_links e
                       JOIN obligations o ON e.obligation_id = o.obligation_id 
                       WHERE o.document_id = $1""",
                    doc_id
                )
                print(f"   - Evidence links: {evidence_count}")
                
                return True
            else:
                print(f"❌ Document {doc_id} not found in database")
                return False
                
        finally:
            await conn.close()
    
    return asyncio.run(check_db())

if __name__ == "__main__":
    print("=== Full Pipeline Test ===")
    
    # Test document processing
    result = test_document_processing()
    
    if result and result.get('document_id'):
        # Verify database storage
        verify_database_storage(result['document_id'])
    
    print("\n✨ Test completed!")