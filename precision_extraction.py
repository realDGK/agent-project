"""
Precision extraction module using contract-specific schemas
Implements the exact extraction quality expected from Gemini
"""
import json
import logging
import re
from typing import Dict, Any
import google.generativeai as genai
from contract_schemas import (
    EXTRACTION_PRE_PROMPT,
    get_schema_for_contract_type,
    detect_contract_type
)

logger = logging.getLogger(__name__)

def extract_with_precision(content: str, filename: str) -> Dict[str, Any]:
    """
    High-precision extraction using contract-specific schemas
    This should match the quality you get from Gemini web chat
    """
    try:
        # Step 1: Detect contract type
        contract_type = detect_contract_type(content)
        logger.info(f"Detected contract type: {contract_type}")
        
        # Step 2: Get appropriate schema
        schema = get_schema_for_contract_type(contract_type)
        
        # Step 3: Build the extraction prompt with pre-prompt
        prompt = f"""{EXTRACTION_PRE_PROMPT}

JSON SCHEMA TO POPULATE:
{json.dumps(schema, indent=2)}

DOCUMENT TEXT TO ANALYZE:
{content[:12000]}
"""
        
        # Step 4: Call Gemini with the precision prompt
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Step 5: Parse the response
        try:
            # The model should return pure JSON based on our instructions
            result = json.loads(response.text.strip())
            
            # Step 6: Transform to our standard format
            standardized = transform_to_standard_format(result, contract_type)
            
            logger.info(f"Precision extraction successful for {contract_type}")
            return standardized
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Fallback to regex extraction from response
            return parse_response_fallback(response.text, schema)
            
    except Exception as e:
        logger.error(f"Precision extraction failed: {e}")
        return {"error": str(e)}

def transform_to_standard_format(extracted_data: Dict, contract_type: str) -> Dict[str, Any]:
    """
    Transform the schema-based extraction to our standard format
    This ensures compatibility with the existing UI
    """
    result = {
        "document_type": {
            "type": contract_type,
            "confidence": 0.95
        },
        "parties": [],
        "financial_terms": [],
        "dates": [],
        "property_details": {},
        "discovered_entities": extracted_data.get("discovered_entities", []),
        "confidence_score": 0.90
    }
    
    # Extract parties
    if "parties" in extracted_data:
        for role, party_info in extracted_data["parties"].items():
            if party_info and party_info.get("name"):
                result["parties"].append({
                    "role": role.replace("_", " ").title(),
                    "full_name": party_info["name"],
                    "entity_type": party_info.get("entity_type"),
                    "representative": party_info.get("representative"),
                    "confidence": 0.95
                })
    
    # Extract financial terms based on contract type
    if "financial_terms" in extracted_data:
        for key, value in extracted_data["financial_terms"].items():
            if value is not None:
                # Handle different value types
                if isinstance(value, (int, float)):
                    amount = value
                elif isinstance(value, str):
                    # Extract number from string
                    amount_match = re.search(r'[\d,]+(?:\.\d+)?', value.replace('$', ''))
                    amount = float(amount_match.group().replace(',', '')) if amount_match else 0
                else:
                    continue
                    
                result["financial_terms"].append({
                    "amount": amount,
                    "description": key.replace("_", " ").title(),
                    "type": key,
                    "confidence": 0.90
                })
    
    # Handle lease-specific financial terms
    if "lease_terms" in extracted_data and "financial_terms" in extracted_data["lease_terms"]:
        for key, value in extracted_data["lease_terms"]["financial_terms"].items():
            if value is not None:
                result["financial_terms"].append({
                    "amount": parse_amount(value),
                    "description": key.replace("_", " ").title(),
                    "type": key,
                    "confidence": 0.90
                })
    
    # Extract dates and periods
    if "dates_and_periods" in extracted_data:
        for key, value in extracted_data["dates_and_periods"].items():
            if value:
                result["dates"].append({
                    "date": value,
                    "description": key.replace("_", " ").title(),
                    "type": key,
                    "confidence": 0.90
                })
    elif "dates_and_deadlines" in extracted_data:
        for key, value in extracted_data["dates_and_deadlines"].items():
            if value:
                result["dates"].append({
                    "date": value,
                    "description": key.replace("_", " ").title(),
                    "type": key,
                    "confidence": 0.90
                })
    
    # Extract property details
    if "property" in extracted_data:
        result["property_details"] = extracted_data["property"]
    elif "leased_premises" in extracted_data:
        result["property_details"] = extracted_data["leased_premises"]
    
    return result

def parse_amount(value) -> float:
    """
    Parse amount from various formats
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.,]', '', value)
        cleaned = cleaned.replace(',', '')
        try:
            return float(cleaned)
        except:
            return 0.0
    return 0.0

def parse_response_fallback(response_text: str, schema: Dict) -> Dict[str, Any]:
    """
    Fallback parser if JSON parsing fails
    Attempts to extract data using patterns
    """
    result = {
        "document_type": {"type": "unknown", "confidence": 0.60},
        "parties": [],
        "financial_terms": [],
        "dates": [],
        "property_details": {},
        "confidence_score": 0.60
    }
    
    # Try to find parties
    party_patterns = [
        r'(?:purchaser|buyer|seller|lessor|lessee|landlord|tenant)[\s:]+([A-Z][A-Za-z\s,&.]+(?:LLC|Inc|Corp)?)',
        r'"name":\s*"([^"]+)"'
    ]
    
    for pattern in party_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        for match in matches:
            if match and len(match) > 3:
                result["parties"].append({
                    "full_name": match.strip(),
                    "confidence": 0.70
                })
    
    # Try to find amounts
    amount_pattern = r'\$?([\d,]+(?:\.\d{2})?)'
    amounts = re.findall(amount_pattern, response_text)
    for amount_str in amounts:
        try:
            amount = float(amount_str.replace(',', ''))
            if amount > 100:  # Filter out small numbers
                result["financial_terms"].append({
                    "amount": amount,
                    "description": "Extracted Amount",
                    "confidence": 0.60
                })
        except:
            pass
    
    # Try to find dates
    date_patterns = [
        r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})'
    ]
    
    for pattern in date_patterns:
        dates = re.findall(pattern, response_text)
        for date_str in dates:
            result["dates"].append({
                "date": date_str,
                "confidence": 0.70
            })
    
    return result

# Enhanced extraction for better quality
def extract_with_enhanced_precision(content: str, filename: str) -> Dict[str, Any]:
    """
    Enhanced version with two-stage extraction for maximum accuracy
    First pass: Get structured data
    Second pass: Validate and enrich
    """
    try:
        # First extraction
        initial_result = extract_with_precision(content, filename)
        
        if initial_result.get("error"):
            return initial_result
        
        # Second pass: Ask for validation and missing items
        validation_prompt = f"""
        I extracted the following data from a {filename}:
        {json.dumps(initial_result, indent=2)}
        
        Please review the document again and:
        1. Correct any errors in the extraction
        2. Add any missing critical information
        3. Ensure all dollar amounts have proper context (not just "extracted_amount")
        4. Ensure all dates have proper context (what the date represents)
        
        Document excerpt:
        {content[:3000]}
        
        Return the corrected JSON with the same structure.
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(validation_prompt)
        
        try:
            # Clean response
            response_text = response.text.strip()
            if '```' in response_text:
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*', '', response_text)
            
            validated = json.loads(response_text)
            validated["confidence_score"] = 0.95  # Higher confidence after validation
            return validated
            
        except:
            # If validation fails, return initial result
            return initial_result
            
    except Exception as e:
        logger.error(f"Enhanced extraction failed: {e}")
        return {"error": str(e)}