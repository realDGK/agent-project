#!/usr/bin/env python3
import requests
import json

def test_noisy_docx_content():
    """Test with content that simulates what happens when DOCX is read as text"""
    
    # Simulate noisy DOCX content (like what FileReader.readAsText produces)
    noisy_content = """
PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00word/_rels/.relsword/document.xml<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>LETTER OF INTENT</w:t></w:r></w:p>
<w:p><w:r><w:t>This Letter of Intent is entered into between COYNE DEVELOPMENT LLC, a California limited liability company (Buyer) and MOSSDALE HOLDINGS CORP (Seller).</w:t></w:r></w:p>
<w:p><w:r><w:t>PURCHASE PRICE: The proposed purchase price is TWO MILLION FIVE HUNDRED THOUSAND DOLLARS ($2,500,000.00) for the Property located at 1234 Industrial Way, Lathrop, CA.</w:t></w:r></w:p>
<w:p><w:r><w:t>EARNEST MONEY: Buyer shall deposit FIFTY THOUSAND DOLLARS ($50,000.00) as earnest money within five (5) business days.</w:t></w:r></w:p>
<w:p><w:r><w:t>DUE DILIGENCE PERIOD: Buyer shall have sixty (60) days to complete due diligence.</w:t></w:r></w:p>
<w:p><w:r><w:t>CONTINGENCIES: This offer is contingent upon satisfactory environmental assessment and zoning approval.</w:t></w:r></w:p>
<w:p><w:r><w:t>BROKER: RE/MAX Commercial Services shall receive a commission of 2.5% of the purchase price.</w:t></w:r></w:p>
<w:p><w:r><w:t>EXPIRATION: This Letter of Intent expires on December 31, 2024.</w:t></w:r></w:p>
<w:p><w:r><w:t>COYNE DEVELOPMENT LLC</w:t></w:r></w:p>
<w:p><w:r><w:t>By: Michael Coyne, Managing Member</w:t></w:r></w:p>
<w:p><w:r><w:t>MOSSDALE HOLDINGS CORP</w:t></w:r></w:p>
<w:p><w:r><w:t>By: Sarah Johnson, President</w:t></w:r></w:p>
</w:body>
</w:document>
PKword/styles.xmlPKword/fontTable.xmlPKword/webSettings.xmlPK\x01\x02-\x00
""" + "garbage_data_here" * 1000  # Make it 111K+ characters like the real file

    print(f"Testing with noisy content ({len(noisy_content)} characters)")
    print(f"First 200 chars: {repr(noisy_content[:200])}")
    
    try:
        response = requests.post('http://localhost:8000/api/analyze-document', 
                               json={
                                   'content': noisy_content,
                                   'filename': 'Coyne_LOI_Noisy.docx'
                               },
                               timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis successful!")
            print(f"Document ID: {result['document_id']}")
            print(f"Confidence: {result['confidence_score']}")
            print(f"HIL Required: {result['requires_human_review']}")
            
            metadata = result['extracted_metadata']
            print(f"Analysis Method: {metadata.get('analysis_method', 'unknown')}")
            print(f"Content Length: {metadata.get('content_length', 0)} chars")
            
            # Check parties
            parties = metadata.get('parties', [])
            print(f"\nParties found: {len(parties)}")
            for i, party in enumerate(parties[:5]):
                text = party.get('text', '')[:60]
                role = party.get('role', 'unknown')
                conf = party.get('confidence', 0)
                print(f"  {i+1}. '{text}...' (role: {role}, conf: {conf:.2f})")
            
            # Check financial terms
            financial = metadata.get('financial_terms', [])
            print(f"\nFinancial terms: {len(financial)}")
            for i, term in enumerate(financial[:5]):
                amount = term.get('amount', 0)
                term_type = term.get('type', term.get('label', 'unknown'))
                conf = term.get('confidence', 0)
                print(f"  {i+1}. ${amount:,.2f} ({term_type}) (conf: {conf:.2f})")
            
            # Check if content was cleaned
            if 'note' in metadata:
                print(f"⚠️  Note: {metadata['note']}")
                
            # Check for meaningful extraction
            meaningful_parties = [p for p in parties if 'coyne' in p.get('text', '').lower() or 'mossdale' in p.get('text', '').lower()]
            meaningful_amounts = [f for f in financial if f.get('amount', 0) > 1000]
            
            print(f"\n📊 Quality Assessment:")
            print(f"   Found meaningful parties: {len(meaningful_parties)}")
            print(f"   Found significant amounts: {len(meaningful_amounts)}")
            
            if len(meaningful_parties) >= 2 and len(meaningful_amounts) >= 2:
                print("✅ Content cleaning and extraction working well!")
            else:
                print("❌ Still not extracting meaningful data properly")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_noisy_docx_content()