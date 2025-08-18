"""
Production database persistence for AI extraction results
Maps model output → DB payload and calls apply_extraction()
"""
import asyncio
import asyncpg
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def persist_extraction(db_pool: asyncpg.Pool, doc_id: str, extraction_json: dict, mark_superseded: bool = True) -> None:
    """
    Maps model output → DB payload and calls apply_extraction().
    Compatible with 3-arg function signature with superseded handling.
    """
    p_payload = {
        "extracted_fields": extraction_json.get("extracted_fields", {}),
        "obligations": extraction_json.get("obligations", []),
    }

    async with db_pool.acquire() as conn:
        try:
            # Use the 3-arg signature with superseded handling
            await conn.execute(
                "SELECT apply_extraction($1, $2::jsonb, $3);",
                doc_id, json.dumps(p_payload), mark_superseded
            )
            logger.info(f"Successfully persisted extraction for document {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist extraction for document {doc_id}: {e}")
            raise

def build_db_extraction_payload(ai_result: dict, filename: str) -> dict:
    """
    Convert two-lane AI analysis result to database-compatible format
    """
    # Handle both old regex format and new AI format
    extracted_fields = {}
    obligations = []
    
    if 'extracted_fields' in ai_result:
        extracted_fields = ai_result['extracted_fields']
    else:
        # Convert legacy format if needed
        extracted_fields = {
            "doc_type_guess": ai_result.get('document_type', {}).get('type', 'unknown'),
            "analysis_method": ai_result.get('analysis_method', 'unknown'),
            "confidence_score": ai_result.get('confidence_score', 0.0)
        }
        
        # Convert parties
        if 'parties' in ai_result:
            extracted_fields['parties'] = ai_result['parties']
            
        # Convert financial terms  
        if 'financial_terms' in ai_result:
            extracted_fields['financial_terms'] = ai_result['financial_terms']
            
        # Convert dates
        if 'dates' in ai_result:
            extracted_fields['dates'] = ai_result['dates']
    
    # Extract obligations from AI result
    if 'obligations' in ai_result:
        obligations = ai_result['obligations']
    else:
        # Try to infer obligations from financial terms
        if 'financial_terms' in ai_result:
            for term in ai_result['financial_terms']:
                if isinstance(term, dict) and 'amount' in term:
                    obligations.append({
                        "obligation_type": "make_payment",
                        "description": f"Payment of ${term['amount']:.2f}",
                        "responsible_party": "Undetermined",
                        "status": "open",
                        "evidence": []
                    })
    
    return {
        "extracted_fields": extracted_fields,
        "obligations": obligations
    }