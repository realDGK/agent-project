#!/usr/bin/env python3
"""
Test the fixed extraction to show it properly identifies:
1. The $3.5M purchase price (not missing it)
2. The $19k per lot unit price
3. NOT confusing the $1M insurance as the purchase price
"""

import json
from fixed_extraction import extract_with_fixed_context

# Example content similar to what you described
test_document = """
PURCHASE AND SALE AGREEMENT

This Purchase and Sale Agreement ("Agreement") is entered into as of January 15, 2024,
by and between COYNE DEVELOPMENT LLC, a California limited liability company ("Buyer" or "Purchaser"),
and VALLEY LAND HOLDINGS, INC., a Delaware corporation ("Seller").

RECITALS

WHEREAS, Seller is the owner of certain real property consisting of approximately 184 
approved residential lots located in San Joaquin County, California, as more particularly 
described in Exhibit A attached hereto (the "Property");

WHEREAS, Buyer desires to purchase the Property from Seller, and Seller desires to sell 
the Property to Buyer, upon the terms and conditions set forth herein;

NOW, THEREFORE, in consideration of the mutual covenants and agreements herein contained,
and for other good and valuable consideration, the receipt and sufficiency of which are 
hereby acknowledged, the parties agree as follows:

1. PURCHASE PRICE

   1.1 Total Purchase Price. The total purchase price for the Property shall be 
       THREE MILLION FIVE HUNDRED THOUSAND DOLLARS ($3,500,000.00) (the "Purchase Price"),
       calculated at Nineteen Thousand Dollars ($19,000.00) per lot for the 184 lots.

   1.2 Payment of Purchase Price. The Purchase Price shall be paid as follows:
       
       (a) Earnest Money Deposit. Within three (3) business days after the Effective Date,
           Buyer shall deposit with Chicago Title Company ("Escrow Agent") the sum of
           FIFTY THOUSAND DOLLARS ($50,000.00) as an earnest money deposit.
       
       (b) Additional Deposit. Within ten (10) days after the expiration of the Due 
           Diligence Period, Buyer shall deposit an additional ONE HUNDRED THOUSAND 
           DOLLARS ($100,000.00) with Escrow Agent.
       
       (c) Balance at Closing. The balance of the Purchase Price, in the amount of
           THREE MILLION THREE HUNDRED FIFTY THOUSAND DOLLARS ($3,350,000.00), plus or
           minus prorations and adjustments, shall be paid at Closing.

2. DUE DILIGENCE PERIOD

   2.1 Buyer shall have sixty (60) days from the Effective Date (the "Due Diligence Period")
       to conduct its investigation of the Property.

3. CLOSING

   3.1 The closing of the purchase and sale contemplated by this Agreement ("Closing") 
       shall occur within thirty (30) days after the expiration of the Due Diligence Period.

4. INSURANCE AND INDEMNIFICATION

   4.1 Insurance Requirements. From and after the Closing, Buyer shall maintain, at its 
       sole cost and expense, commercial general liability insurance with respect to the 
       Property with policy limits of not less than ONE MILLION DOLLARS ($1,000,000.00) 
       per occurrence and TWO MILLION DOLLARS ($2,000,000.00) in the aggregate.

   4.2 Builder's Risk Insurance. During any construction on the Property, Buyer shall 
       maintain builder's risk insurance in an amount not less than FIVE MILLION DOLLARS 
       ($5,000,000.00).

5. REPRESENTATIONS AND WARRANTIES

   5.1 Seller's Representations. Seller represents and warrants that:
       (a) Seller has good and marketable title to the Property;
       (b) The Property consists of 184 fully entitled residential lots;
       (c) All development impact fees totaling approximately EIGHT HUNDRED THOUSAND 
           DOLLARS ($800,000.00) have been paid.

6. BROKER'S COMMISSION

   6.1 Seller shall pay a real estate commission to Colliers International in the amount 
       of ONE HUNDRED FIVE THOUSAND DOLLARS ($105,000.00) (3% of the Purchase Price).

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.

BUYER:                                  SELLER:
COYNE DEVELOPMENT LLC,                  VALLEY LAND HOLDINGS, INC.,
a California limited liability company  a Delaware corporation

By: _______________________            By: _______________________
    Michael Coyne, Manager                  James Valley, President
"""

def test_extraction():
    """
    Test the extraction to show it properly identifies amounts
    """
    
    print("="*60)
    print("TESTING FIXED EXTRACTION")
    print("="*60)
    print("\nDocument contains:")
    print("- $3,500,000 total purchase price (THE MAIN DEAL)")
    print("- $19,000 per lot")
    print("- $50,000 earnest money deposit")
    print("- $100,000 additional deposit")
    print("- $1,000,000 insurance requirement (NOT the deal)")
    print("- $5,000,000 builder's risk insurance (NOT the deal)")
    print("- $800,000 impact fees paid")
    print("- $105,000 broker commission")
    print("\n" + "="*60 + "\n")
    
    # Run extraction
    result = extract_with_fixed_context(test_document, "purchase_agreement.pdf")
    
    # Display results
    print("EXTRACTION RESULTS:")
    print("-"*40)
    
    # Check main transaction
    print("\n1. MAIN TRANSACTION VALUE:")
    main_transaction = None
    for term in result.get('financial_terms', []):
        if term.get('is_primary') or term.get('type') == 'main_transaction':
            main_transaction = term
            print(f"   ✓ Found: ${term['amount']:,.2f}")
            print(f"   Description: {term['description']}")
            break
    
    if not main_transaction:
        print("   ✗ MISSING MAIN TRANSACTION VALUE!")
    elif main_transaction['amount'] == 1000000:
        print("   ✗ ERROR: Incorrectly grabbed insurance amount as main deal!")
    elif main_transaction['amount'] == 3500000:
        print("   ✓ CORRECT: Found the actual purchase price!")
    
    # Check all financial terms
    print("\n2. ALL FINANCIAL TERMS FOUND:")
    for term in result.get('financial_terms', []):
        marker = "→" if term.get('is_primary') else " "
        print(f"   {marker} ${term['amount']:,.2f} - {term['description']}")
    
    # Check parties
    print("\n3. PARTIES IDENTIFIED:")
    for party in result.get('parties', []):
        print(f"   {party.get('role', 'Unknown')}: {party.get('full_legal_name', 'Not found')}")
        if party.get('entity_type'):
            print(f"      Type: {party['entity_type']}")
        if party.get('signatory'):
            print(f"      Signed by: {party['signatory']}")
    
    # Check property details
    print("\n4. PROPERTY DETAILS:")
    property_info = result.get('property_details', {})
    if property_info:
        for key, value in property_info.items():
            if value:
                print(f"   {key}: {value}")
    
    # Summary
    print("\n" + "="*60)
    print("EXTRACTION QUALITY CHECK:")
    print("-"*40)
    
    issues = []
    successes = []
    
    # Check for the specific problem mentioned
    has_correct_main = False
    has_insurance_as_main = False
    
    for term in result.get('financial_terms', []):
        if term.get('is_primary') or term.get('type') == 'main_transaction':
            if term['amount'] == 3500000:
                has_correct_main = True
                successes.append("✓ Correctly identified $3.5M as purchase price")
            elif term['amount'] == 1000000:
                has_insurance_as_main = True
                issues.append("✗ Incorrectly used $1M insurance as main value")
    
    if not has_correct_main and not has_insurance_as_main:
        issues.append("✗ Failed to find main transaction value")
    
    # Check for proper party identification
    parties = result.get('parties', [])
    buyer_found = any(p.get('full_legal_name') == 'COYNE DEVELOPMENT LLC' for p in parties)
    seller_found = any(p.get('full_legal_name') == 'VALLEY LAND HOLDINGS, INC.' for p in parties)
    
    if buyer_found:
        successes.append("✓ Correctly identified buyer with full legal name")
    else:
        issues.append("✗ Failed to properly identify buyer")
    
    if seller_found:
        successes.append("✓ Correctly identified seller with full legal name")
    else:
        issues.append("✗ Failed to properly identify seller")
    
    # Print results
    if successes:
        print("\nSUCCESSES:")
        for s in successes:
            print(f"  {s}")
    
    if issues:
        print("\nISSUES FOUND:")
        for i in issues:
            print(f"  {i}")
    
    print("\n" + "="*60)
    
    # Return the result for further processing
    return result

if __name__ == "__main__":
    # Note: This requires GOOGLE_API_KEY to be set
    import os
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("This test requires Gemini API access")
        print("\nTo test without API, the extraction logic will:")
        print("1. Look for 'purchase price' not 'insurance'")
        print("2. Extract full entity names from signature blocks")
        print("3. Label each amount with its purpose")
    else:
        result = test_extraction()
        
        # Save result for inspection
        with open("extraction_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
            print("\nFull result saved to extraction_test_result.json")
