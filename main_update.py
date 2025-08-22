"""
Simple update to use the fixed extraction in main.py
Just replaces the extraction calls with the fixed version
"""

# Add this to your main.py imports:
from fixed_extraction import extract_with_fixed_context

# Then in your analyze_document function, replace the extraction section with:

async def analyze_document_fixed(request: DocumentAnalysisRequest):
    """
    Analyze document with FIXED extraction that properly identifies amounts
    """
    try:
        start_time = datetime.now()
        
        # Clean content
        cleaned_content = clean_content(request.content)
        
        # Create document ID
        pool = await get_db_pool()
        doc_id = str(uuid.uuid4())
        
        # Use FIXED extraction that understands context
        extracted_data = extract_with_fixed_context(cleaned_content, request.filename)
        
        # Check if we got the main transaction
        has_main_transaction = any(
            term.get('is_primary') or term.get('type') == 'main_transaction'
            for term in extracted_data.get('financial_terms', [])
        )
        
        if has_main_transaction:
            logger.info(f"✓ Found main transaction value for {doc_id}")
        else:
            logger.warning(f"⚠ No main transaction value found for {doc_id}")
        
        # Log what we extracted
        logger.info(f"Extraction results for {doc_id}:")
        logger.info(f"  - Parties: {len(extracted_data.get('parties', []))}")
        logger.info(f"  - Financial terms: {len(extracted_data.get('financial_terms', []))}")
        
        for term in extracted_data.get('financial_terms', []):
            if term.get('is_primary'):
                logger.info(f"  - MAIN DEAL: ${term['amount']:,.2f} - {term['description']}")
            else:
                logger.info(f"  - Other: ${term['amount']:,.2f} - {term['description']}")
        
        confidence_score = extracted_data.get('confidence_score', 0.8)
        
        # Persist to database if extraction succeeded
        if extracted_data and not extracted_data.get('error'):
            try:
                success = await persist_with_provenance(
                    pool, doc_id, request.filename, 
                    cleaned_content, extracted_data, confidence_score
                )
                
                if success:
                    logger.info(f"Persisted extraction for document {doc_id}")
                    
                    # Create review task if confidence is low or missing main transaction
                    if confidence_score < 0.8 or not has_main_transaction:
                        await create_review_task_if_needed(
                            pool, doc_id, 
                            hashlib.sha256(cleaned_content.encode()).hexdigest(),
                            confidence_score, extracted_data
                        )
                else:
                    logger.error(f"Failed to persist extraction for {doc_id}")
            except Exception as e:
                logger.error(f"Failed to persist: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DocumentAnalysisResult(
            document_id=doc_id,
            filename=request.filename,
            processing_time=processing_time,
            confidence_score=confidence_score,
            extracted_metadata=extracted_data,
            requires_human_review=confidence_score < 0.8 or not has_main_transaction,
            analysis_timestamp=datetime.now().isoformat(),
            document_text=cleaned_content if len(cleaned_content) < 50000 else None
        )
        
    except Exception as e:
        logger.exception("Document analysis failed")
        raise HTTPException(status_code=500, detail=str(e))
