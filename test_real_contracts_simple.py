#!/usr/bin/env python3
import requests
import json

def test_contract_analysis(content, filename):
    """Test contract analysis with real-like content"""
    print(f"\n=== Testing {filename} ===")
    print(f"Content length: {len(content)} characters")
    print(f"First 200 chars: {content[:200]}...")
    
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
            
            metadata = result['extracted_metadata']
            print(f"Analysis Method: {metadata.get('analysis_method', 'unknown')}")
            
            # Check parties
            parties = metadata.get('parties', [])
            print(f"Parties found: {len(parties)}")
            for i, party in enumerate(parties[:3]):
                text = party.get('text', '')[:50]
                conf = party.get('confidence', 0)
                role = party.get('role', 'unknown')
                print(f"  {i+1}. {text}... (role: {role}, conf: {conf:.2f})")
            
            # Check financial terms
            financial = metadata.get('financial_terms', [])
            print(f"Financial terms: {len(financial)}")
            for i, term in enumerate(financial[:3]):
                amount = term.get('amount', 0)
                term_type = term.get('type', term.get('label', 'unknown'))
                conf = term.get('confidence', 0)
                print(f"  {i+1}. ${amount:,.2f} ({term_type}) (conf: {conf:.2f})")
            
            # Check for errors or issues
            if 'note' in metadata:
                print(f"⚠️  Note: {metadata['note']}")
            
            if result['requires_human_review']:
                hil_reason = metadata.get('hil_reason', 'Unknown reason')
                print(f"🔍 HIL Triggered: {hil_reason}")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    # Test with realistic contract content
    
    # Test 1: Complex PSA with multiple parties and guarantees
    complex_psa = """
    PURCHASE AND SALE AGREEMENT AND ESCROW INSTRUCTIONS
    
    This Purchase and Sale Agreement ("Agreement") is entered into as of March 15, 2024, between LATHROP DEVELOPMENT LLC, a California limited liability company ("Seller"), and MOSSDALE HOLDINGS CORP., a Delaware corporation ("Buyer").
    
    PURCHASE PRICE: The total purchase price for the Property is FIVE MILLION SEVEN HUNDRED FIFTY THOUSAND DOLLARS ($5,750,000.00).
    
    EARNEST MONEY DEPOSIT: Within three (3) business days after execution of this Agreement, Buyer shall deposit with Escrow Agent the sum of TWO HUNDRED FIFTY THOUSAND DOLLARS ($250,000.00) as earnest money.
    
    PERSONAL GUARANTEE: John R. Clevenger ("Guarantor") hereby unconditionally guarantees the performance of all of Buyer's obligations under this Agreement up to a maximum amount of ONE MILLION DOLLARS ($1,000,000.00).
    
    BROKER COMMISSION: Seller agrees to pay a commission of THREE PERCENT (3%) of the purchase price to CENTURY 21 REAL ESTATE SERVICES, totaling ONE HUNDRED SEVENTY-TWO THOUSAND FIVE HUNDRED DOLLARS ($172,500.00).
    
    CLOSING DATE: This transaction shall close on or before June 30, 2024.
    
    CONTINGENCIES: This Agreement is contingent upon Buyer obtaining financing approval by May 1, 2024.
    
    Property Address: 1234 Mossdale Landing Drive, Lathrop, CA 95330
    APN: 203-050-15
    
    Seller's Agent: Maria Rodriguez, Century 21 Real Estate Services
    Buyer's Agent: David Chen, Keller Williams Realty
    
    IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
    
    LATHROP DEVELOPMENT LLC
    By: /s/ Robert Smith
    Robert Smith, Managing Member
    
    MOSSDALE HOLDINGS CORP.
    By: /s/ Jennifer Martinez  
    Jennifer Martinez, President
    
    GUARANTOR:
    /s/ John R. Clevenger
    John R. Clevenger
    """
    
    test_contract_analysis(complex_psa, "Complex_PSA_with_Guarantee.pdf")
    
    # Test 2: Amendment with confusing structure
    amendment = """
    FOURTH AMENDMENT TO DEVELOPMENT AGREEMENT
    
    This Fourth Amendment ("Amendment") to that certain Development Agreement dated January 12, 2018, as previously amended ("Original Agreement"), is entered into as of May 9, 2018, between the CITY OF LATHROP, a municipal corporation ("City"), and RAMONA CHACE SCHUSSING, an individual ("Developer").
    
    WHEREAS, the parties desire to modify certain terms of the Original Agreement regarding payment schedules and bond assumptions;
    
    NOW THEREFORE, the Original Agreement is hereby amended as follows:
    
    1. PARTIAL PAYOFF: Developer shall make a partial payoff in the amount of EIGHT HUNDRED THOUSAND DOLLARS ($800,000.00) on or before May 15, 2018.
    
    2. BOND ASSUMPTION: Developer hereby assumes responsibility for the Nuriso Infrastructure Bond in the original principal amount of TWO MILLION FOUR HUNDRED THOUSAND DOLLARS ($2,400,000.00), with current outstanding balance of approximately ONE MILLION EIGHT HUNDRED THOUSAND DOLLARS ($1,800,000.00).
    
    3. REVISED TIMELINE: All development milestones under Section 4.2 of the Original Agreement are hereby extended by six (6) months.
    
    4. GUARANTOR LIABILITY: The personal guarantee provided by Ramona Chace Schussing under the Original Agreement shall be reduced from $5,000,000 to THREE MILLION DOLLARS ($3,000,000.00) upon completion of the partial payoff described in Section 1 above.
    
    All other terms of the Original Agreement remain in full force and effect.
    
    CITY OF LATHROP
    By: /s/ Steven Salvatore
    Steven Salvatore, City Manager
    
    DEVELOPER:
    /s/ Ramona Chace Schussing  
    Ramona Chace Schussing
    """
    
    test_contract_analysis(amendment, "Ramona_Chace_Fourth_Amendment.pdf")
    
    # Test 3: Poor quality / scanned document simulation
    poor_quality = """
    LEASE AGREEMENT
    
    Th1s l3ase agr33m3nt 1s b3tw33n... [OCR artifacts and unclear text]
    
    Landlord: ABC Prop3rt13s LLC... unclear signature
    Tenant: XYZ Corp0rat1on... smudged text
    
    M0nthly R3nt: $... [amount unclear due to poor scan quality]
    S3cur1ty D3p0s1t: $... [partially visible]
    
    L3as3 T3rm: Start1ng... [date unclear] through... [end date unclear]
    
    [Multiple lines of garbled text due to poor OCR quality]
    
    Th1s d0cum3nt c0nta1ns 1mp0rtant 1nf0rmat10n but may r3qu1r3 manual r3v13w du3 t0 p00r scan qual1ty.
    """
    
    test_contract_analysis(poor_quality, "Poor_Quality_Scan_Lease.pdf")