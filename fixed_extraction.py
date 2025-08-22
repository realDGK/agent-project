"""
Fixed extraction module - focuses on CONTEXT and MEANING
Solves the problem of grabbing wrong numbers and missing important ones
"""
import json
import logging
import re
from typing import Dict, Any, List, Tuple
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ContextAwareExtractor:
    """
    Extraction that understands CONTEXT of numbers and names
    Not just pattern matching
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro')  # Better for long context
        
    def extract_with_context(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Main extraction method that focuses on MEANING not just patterns
        """
        
        # Step 1: First understand what kind of document this is
        doc_understanding = self.understand_document(content, filename)
        
        # Step 2: Extract with context awareness
        extraction = self.extract_meaningful_data(content, doc_understanding)
        
        # Step 3: Validate and fix common errors
        validated = self.validate_extraction(extraction, content)
        
        return validated
    
    def understand_document(self, content: str, filename: str) -> Dict:
        """
        First understand what this document is about
        """
        prompt = f"""
        Read this document and tell me:
        1. What TYPE of transaction is this? (sale, lease, loan, etc.)
        2. What is the MAIN DEAL VALUE? (the primary transaction amount)
        3. Who are the PRINCIPAL PARTIES? (buyer/seller, landlord/tenant, etc.)
        4. What is being transacted? (property, business, etc.)
        
        Document: {content[:3000]}
        
        Answer in JSON:
        {{
            "transaction_type": "...",
            "main_deal_value": "...",
            "principal_parties": [...],
            "transaction_subject": "..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            understanding = self.parse_json_response(response.text)
            logger.info(f"Document understanding: {understanding}")
            return understanding
        except Exception as e:
            logger.error(f"Failed to understand document: {e}")
            return {}
    
    def extract_meaningful_data(self, content: str, understanding: Dict) -> Dict:
        """
        Extract data with focus on MEANING and CONTEXT
        """
        
        # Build a context-aware prompt
        prompt = f"""
        You are extracting data from a {understanding.get('transaction_type', 'real estate')} document.
        The main transaction value should be around {understanding.get('main_deal_value', 'unknown')}.
        
        CRITICAL RULES:
        1. For EVERY dollar amount, you MUST identify what it's for:
           - Is it the purchase price? (THE MAIN DEAL VALUE)
           - Is it a deposit?
           - Is it an insurance requirement? (NOT the deal value)
           - Is it a fee?
           - Is it something else?
        
        2. For the main purchase/lease/loan amount:
           - Look for "purchase price", "total price", "consideration"
           - This is usually the BIGGEST number related to the actual transaction
           - NOT insurance requirements, NOT liability limits
        
        3. For parties:
           - Get the FULL LEGAL NAME (e.g., "Coyne Development LLC" not just "Coyne")
           - Identify their ROLE (Buyer, Seller, Landlord, Tenant, etc.)
           - Look for signature blocks - they have the official names
        
        4. CONTEXT CLUES for amounts:
           - "Purchase price" or "total consideration" = MAIN DEAL
           - "Insurance" or "liability" = NOT the deal, just a requirement
           - "Deposit" or "earnest money" = Part of deal but not total
           - "Per lot" or "per unit" = Unit price, multiply for total
        
        Document to analyze:
        {content[:8000]}
        
        Extract and return JSON:
        {{
            "main_transaction": {{
                "total_value": null,  // The MAIN deal value
                "value_description": null,  // What this value represents
                "unit_price": null,  // Price per unit if applicable
                "units": null  // Number of units
            }},
            "parties": [
                {{
                    "role": null,  // Buyer, Seller, etc.
                    "full_legal_name": null,  // Complete entity name
                    "entity_type": null,  // LLC, Corp, Individual
                    "signatory": null  // Who signed for them
                }}
            ],
            "other_financial_terms": [
                {{
                    "amount": null,
                    "description": null,  // WHAT this amount is for
                    "category": null  // deposit, fee, insurance, etc.
                }}
            ],
            "property": {{
                "description": null,
                "address": null,
                "lots_or_units": null
            }},
            "important_dates": [
                {{
                    "date": null,
                    "description": null  // WHAT this date represents
                }}
            ]
        }}
        
        REMEMBER: 
        - Insurance requirements are NOT the purchase price
        - Get the ACTUAL DEAL VALUE, not random numbers
        - Every amount needs a description of what it's for
        """
        
        try:
            response = self.model.generate_content(prompt)
            extraction = self.parse_json_response(response.text)
            
            # Log what we found for debugging
            if extraction.get('main_transaction'):
                logger.info(f"Main transaction: {extraction['main_transaction']}")
            
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return self.fallback_extraction(content)
    
    def validate_extraction(self, extraction: Dict, content: str) -> Dict:
        """
        Validate and fix common extraction errors
        """
        
        # Check if we have the main transaction value
        main_value = extraction.get('main_transaction', {}).get('total_value')
        
        if not main_value:
            # Try to find it with targeted search
            main_value = self.find_main_transaction_value(content)
            if main_value:
                extraction['main_transaction'] = extraction.get('main_transaction', {})
                extraction['main_transaction']['total_value'] = main_value
                extraction['main_transaction']['value_description'] = "Purchase Price (recovered)"
        
        # Validate party names aren't fragments
        parties = extraction.get('parties', [])
        for party in parties:
            if party.get('full_legal_name'):
                # Check if it looks like a fragment
                name = party['full_legal_name']
                if len(name.split()) == 1 and not any(suffix in name.upper() for suffix in ['LLC', 'INC', 'CORP']):
                    # Likely a fragment, try to find full name
                    full_name = self.find_full_party_name(content, name)
                    if full_name:
                        party['full_legal_name'] = full_name
        
        # Remove insurance amounts from main deal if they snuck in
        if main_value and isinstance(main_value, (int, float)):
            # Check if this might be an insurance amount
            if 'insurance' in str(extraction.get('main_transaction', {}).get('value_description', '')).lower():
                # This is wrong, move it to other terms
                extraction['other_financial_terms'] = extraction.get('other_financial_terms', [])
                extraction['other_financial_terms'].append({
                    'amount': main_value,
                    'description': 'Insurance Requirement',
                    'category': 'insurance'
                })
                extraction['main_transaction']['total_value'] = None
                
                # Try again to find the real value
                real_value = self.find_main_transaction_value(content)
                if real_value:
                    extraction['main_transaction']['total_value'] = real_value
        
        # Add confidence scores
        extraction['confidence_score'] = self.calculate_confidence(extraction)
        
        return extraction
    
    def find_main_transaction_value(self, content: str) -> float:
        """
        Targeted search for the main transaction value
        """
        
        # Patterns that indicate the MAIN deal value
        main_value_patterns = [
            r'(?:total\s+)?purchase\s+price[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'(?:total\s+)?consideration[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'agrees\s+to\s+pay[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'(?:total\s+)?sale\s+price[:\s]+\$?([\d,]+(?:\.\d{2})?)',
            r'(?:aggregate\s+)?price\s+of\s+\$?([\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in main_value_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.replace(',', ''))
                    # Sanity check - main deal usually > $100k for real estate
                    if value > 100000:
                        logger.info(f"Found main transaction value: ${value:,.2f}")
                        return value
                except:
                    continue
        
        # If not found with patterns, look for the largest sensible value
        all_amounts = re.findall(r'\$?([\d,]+(?:\.\d{2})?)', content)
        valid_amounts = []
        
        for amount_str in all_amounts:
            try:
                value = float(amount_str.replace(',', ''))
                # Exclude common non-deal amounts
                if 100000 < value < 100000000:  # Between $100k and $100M
                    # Check context around this amount
                    index = content.find(amount_str)
                    context = content[max(0, index-100):min(len(content), index+100)].lower()
                    
                    # Skip if it's insurance, liability, etc.
                    if not any(skip in context for skip in ['insurance', 'liability', 'coverage', 'limit', 'bond']):
                        valid_amounts.append(value)
            except:
                continue
        
        if valid_amounts:
            # Return the largest amount that's not insurance
            return max(valid_amounts)
        
        return None
    
    def find_full_party_name(self, content: str, fragment: str) -> str:
        """
        Find the full legal name when we only have a fragment
        """
        
        # Look for the fragment with common suffixes
        patterns = [
            rf'{re.escape(fragment)}\s+[\w\s]*(?:LLC|Inc|Corp|Company|LP|LLP|Partnership)',
            rf'(?:by|between|from|to):\s*{re.escape(fragment)}[\w\s]*(?:LLC|Inc|Corp)',
            rf'{re.escape(fragment)}[\w\s]*,\s+a\s+[\w\s]+(?:limited liability company|corporation)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Return the longest match (likely most complete)
                return max(matches, key=len).strip()
        
        # Check signature blocks
        sig_pattern = rf'By:\s*_+\s*{re.escape(fragment)}[\w\s]*'
        sig_matches = re.findall(sig_pattern, content, re.IGNORECASE)
        if sig_matches:
            return sig_matches[0].replace('By:', '').replace('_', '').strip()
        
        return fragment  # Return original if we can't find full name
    
    def calculate_confidence(self, extraction: Dict) -> float:
        """
        Calculate confidence score based on what we found
        """
        score = 0.5  # Base score
        
        # Main transaction value found
        if extraction.get('main_transaction', {}).get('total_value'):
            score += 0.2
        
        # Parties with full names
        parties = extraction.get('parties', [])
        if parties:
            full_names = [p for p in parties if p.get('full_legal_name') and len(p['full_legal_name'].split()) > 1]
            if full_names:
                score += 0.15
        
        # Financial terms with descriptions
        other_terms = extraction.get('other_financial_terms', [])
        described_terms = [t for t in other_terms if t.get('description') and t['description'] != 'extracted_amount']
        if described_terms:
            score += 0.1
        
        # Property details
        if extraction.get('property', {}).get('description'):
            score += 0.05
        
        return min(score, 0.95)
    
    def fallback_extraction(self, content: str) -> Dict:
        """
        Fallback to simpler extraction if main method fails
        """
        
        prompt = f"""
        Extract from this document:
        
        1. What is being sold/leased/financed and for how much total?
        2. Who is the buyer/tenant/borrower? (full legal name)
        3. Who is the seller/landlord/lender? (full legal name)
        4. What are the other important amounts? (deposits, fees, etc.)
        
        Document: {content[:4000]}
        
        Be specific about what each amount represents.
        Return as JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_json_response(response.text)
        except:
            return {"error": "Extraction failed"}
    
    def parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from response, handling common issues
        """
        
        # Remove markdown formatting
        cleaned = response_text.strip()
        if '```json' in cleaned:
            cleaned = cleaned.split('```json')[1].split('```')[0]
        elif '```' in cleaned:
            cleaned = cleaned.split('```')[1].split('```')[0]
        
        # Remove any text before the first {
        if '{' in cleaned:
            cleaned = cleaned[cleaned.index('{'):]
        
        # Remove any text after the last }
        if '}' in cleaned:
            cleaned = cleaned[:cleaned.rindex('}')+1]
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Attempted to parse: {cleaned[:500]}")
            
            # Try to fix common issues
            # Remove trailing commas
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            
            try:
                return json.loads(cleaned)
            except:
                return {}

# Main function to use
def extract_with_fixed_context(content: str, filename: str) -> Dict[str, Any]:
    """
    Main entry point for fixed extraction
    """
    extractor = ContextAwareExtractor()
    result = extractor.extract_with_context(content, filename)
    
    # Transform to your expected format
    transformed = {
        "document_type": {
            "type": result.get('transaction_type', 'unknown'),
            "confidence": result.get('confidence_score', 0.7)
        },
        "parties": result.get('parties', []),
        "financial_terms": [],
        "dates": result.get('important_dates', []),
        "property_details": result.get('property', {}),
        "confidence_score": result.get('confidence_score', 0.7)
    }
    
    # Add main transaction as primary financial term
    if result.get('main_transaction', {}).get('total_value'):
        transformed['financial_terms'].append({
            "amount": result['main_transaction']['total_value'],
            "description": result['main_transaction'].get('value_description', 'Total Purchase Price'),
            "type": "main_transaction",
            "is_primary": True
        })
        
        # Add unit price if present
        if result['main_transaction'].get('unit_price'):
            transformed['financial_terms'].append({
                "amount": result['main_transaction']['unit_price'],
                "description": f"Price per {result['main_transaction'].get('units', 'unit')}",
                "type": "unit_price"
            })
    
    # Add other financial terms
    for term in result.get('other_financial_terms', []):
        if term.get('amount') and term.get('description'):
            transformed['financial_terms'].append({
                "amount": term['amount'],
                "description": term['description'],
                "type": term.get('category', 'other')
            })
    
    return transformed

if __name__ == "__main__":
    # Test the extraction
    test_content = """
    PURCHASE AND SALE AGREEMENT
    
    This Agreement is between Coyne Development LLC ("Buyer") and 
    Smith Properties Inc, a California corporation ("Seller").
    
    Purchase Price: The total purchase price for the Property shall be 
    Three Million Five Hundred Thousand Dollars ($3,500,000), calculated 
    as follows: $19,000 per lot for 184 lots.
    
    Deposit: Buyer shall deposit $50,000 as earnest money.
    
    Insurance: Buyer shall maintain liability insurance of not less than 
    $1,000,000 per occurrence.
    """
    
    result = extract_with_fixed_context(test_content, "test_psa.pdf")
    print(json.dumps(result, indent=2))
