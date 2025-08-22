"""
Ultra-simple extraction that lets Gemini do what it does best
"""
import re
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

def extract_with_gemini_simple(content: str, filename: str) -> dict:
    """
    Dead simple extraction - just ask Gemini to do better
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # SUPER SIMPLE PROMPT - just like what worked for you
        prompt = f"""
        I need to extract data from this {filename} document.
        
        Please extract:
        - All parties with their roles (Buyer, Seller, Escrow Agent, etc.)
        - All financial amounts with what they're for (not just "extracted_amount")
        - All dates with what they represent
        - Property details
        
        Here's the document:
        {content[:8000]}
        
        Please provide well-structured JSON with meaningful labels for everything.
        Can you do better than just "extracted_amount" and actually tell me what each amount is for?
        """
        
        response = model.generate_content(prompt)
        
        try:
            response_text = response.text.strip()
            # Clean up any markdown formatting
            if '```' in response_text:
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*', '', response_text)
            
            result = json.loads(response_text)
            logger.info("Simple extraction successful")
            return result
            
        except json.JSONDecodeError:
            # Try another simple approach
            return extract_with_natural_language(content, filename, response.text)
            
    except Exception as e:
        logger.error(f"Simple extraction failed: {e}")
        return {"error": str(e)}


def extract_with_natural_language(content: str, filename: str, previous_response: str = None) -> dict:
    """
    Even simpler - just ask in natural language and parse the response
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        Look at this {filename} and tell me:
        
        1. Who are the parties? (full names and their roles)
        2. What are the dollar amounts and what is each one for?
        3. What are the important dates and deadlines?
        4. What property is involved?
        
        Document:
        {content[:6000]}
        
        Format your answer as JSON.
        """
        
        response = model.generate_content(prompt)
        
        # Try to parse as JSON
        try:
            response_text = response.text.strip()
            if '```' in response_text:
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*', '', response_text)
            
            return json.loads(response_text)
        except:
            # If JSON fails, parse the text response
            return parse_natural_language_response(response.text, content)
            
    except Exception as e:
        logger.error(f"Natural language extraction failed: {e}")
        return {"error": str(e)}


def parse_natural_language_response(response_text: str, content: str) -> dict:
    """
    Parse a natural language response into structured data
    """
    result = {
        "parties": [],
        "financial_terms": [],
        "dates": [],
        "property": {},
        "confidence_score": 0.85
    }
    
    lines = response_text.split('\n')
    
    current_section = None
    for line in lines:
        line_lower = line.lower()
        
        # Detect sections
        if 'parties' in line_lower or 'who are' in line_lower:
            current_section = 'parties'
        elif 'amount' in line_lower or 'dollar' in line_lower or 'financial' in line_lower:
            current_section = 'financial'
        elif 'date' in line_lower or 'deadline' in line_lower:
            current_section = 'dates'
        elif 'property' in line_lower:
            current_section = 'property'
        
        # Extract based on section
        if current_section == 'parties':
            # Look for patterns like "Buyer: Coyne Development LLC"
            party_match = re.search(r'(Buyer|Seller|Purchaser|Landlord|Tenant|Escrow|Title|Agent|Broker)[:\s-]+([A-Z][A-Za-z\s&,\.]+(?:LLC|Inc|Corp|Company)?)', line)
            if party_match:
                result['parties'].append({
                    "role": party_match.group(1),
                    "name": party_match.group(2).strip(),
                    "confidence": 0.90
                })
        
        elif current_section == 'financial':
            # Look for dollar amounts with context
            money_matches = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)\s*(?:[-–]\s*)?([A-Za-z\s]+)', line)
            for amount_str, description in money_matches:
                amount = float(amount_str.replace(',', ''))
                result['financial_terms'].append({
                    "amount": amount,
                    "label": description.strip(),
                    "confidence": 0.85
                })
        
        elif current_section == 'dates':
            # Look for dates
            date_patterns = [
                r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d+\s*days?)',
                r'(\d+\s*months?)'
            ]
            for pattern in date_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    result['dates'].append({
                        "text": match,
                        "context": line[:100],
                        "confidence": 0.80
                    })
    
    return result


def two_stage_extraction(content: str, filename: str) -> dict:
    """
    Two-stage approach: First get natural extraction, then ask for improvement
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Stage 1: Basic extraction
        initial_prompt = f"""
        Extract key information from this {filename}:
        {content[:4000]}
        
        Return as JSON with parties, amounts, dates, and property info.
        """
        
        initial_response = model.generate_content(initial_prompt)
        
        # Stage 2: Ask for improvement (like you did)
        improvement_prompt = f"""
        Here's an extraction from a contract, but it's not very good:
        {initial_response.text}
        
        Can you do better? Specifically:
        - Use full legal names for parties, not fragments
        - Label each dollar amount with what it's actually for (not "extracted_amount")
        - Explain what each date represents
        - Include property details
        
        Return improved JSON.
        """
        
        improved_response = model.generate_content(improvement_prompt)
        
        try:
            response_text = improved_response.text.strip()
            if '```' in response_text:
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*', '', response_text)
            
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            logger.warning("JSON decode failed, using simpler approach")
            return extract_with_gemini_simple(content, filename)
            
    except Exception as e:
        logger.error(f"Two-stage extraction failed: {e}")
        return extract_with_gemini_simple(content, filename)