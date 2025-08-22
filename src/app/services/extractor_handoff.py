"""
Extraction prompt bundle builder
"""
import os
import json
import hashlib
from typing import Dict, Tuple
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from improved_loader import SchemaLoader

# Pre-prompt for high-quality extraction
EXTRACTION_PRE_PROMPT = """You are a contract extraction specialist. Your task is to extract structured data from the provided document according to the given JSON schema.

CRITICAL INSTRUCTIONS:
1. Extract ONLY what is explicitly stated in the document
2. Use null for missing/unclear information
3. Preserve exact wording for direct quotes
4. Include page numbers and context when available
5. Focus on accuracy over completeness

OUTPUT REQUIREMENTS:
- Return ONLY a valid JSON object matching the provided schema
- No explanations or commentary
- Use proper JSON formatting with double quotes
"""

def normalize_slug(label: str) -> str:
    """Normalize a label to slug format"""
    # Handle common variations
    label = label.lower().strip()
    
    # Replace spaces and underscores with hyphens
    label = label.replace(" ", "-").replace("_", "-")
    
    # Remove parentheses and their contents for matching
    import re
    label = re.sub(r'\([^)]*\)', '', label).strip()
    
    # Common mappings
    mappings = {
        "psa": "purchase-sale-agreement-psa",
        "loi": "letter-of-intent-loi",
        "nda": "non-disclosure-agreement-nda",
        "purchase-sale-agreement": "purchase-sale-agreement-psa",
        "letter-of-intent": "letter-of-intent-loi",
        "non-disclosure-agreement": "non-disclosure-agreement-nda",
    }
    
    if label in mappings:
        return mappings[label]
    
    # Clean up multiple hyphens
    label = re.sub(r'-+', '-', label).strip('-')
    
    return label

def build_prompt_bundle(slug_or_label: str, base_schema_path: str = None) -> Tuple[str, Dict]:
    """
    Build a complete prompt bundle for extraction
    
    Args:
        slug_or_label: Document type slug or label to normalize
        base_schema_path: Optional path to base schema
    
    Returns:
        (prompt_text, metadata_dict)
    """
    # Normalize the input to a slug
    slug = normalize_slug(slug_or_label)
    
    # Load schema using our improved loader
    loader = SchemaLoader()
    
    try:
        schema, few_shot_examples, meta = loader.load_for_doc_type(slug, base_schema_path)
    except FileNotFoundError as e:
        # Try without normalization if normalized version fails
        if slug != slug_or_label:
            schema, few_shot_examples, meta = loader.load_for_doc_type(slug_or_label, base_schema_path)
            slug = slug_or_label
        else:
            raise e
    
    # Build the complete prompt
    prompt_parts = [EXTRACTION_PRE_PROMPT]
    
    # Add schema definition
    prompt_parts.append("\n# JSON SCHEMA")
    prompt_parts.append(json.dumps(schema, indent=2))
    
    # Add few-shot examples if available
    if few_shot_examples:
        prompt_parts.append("\n# FEW-SHOT EXAMPLES")
        prompt_parts.append(few_shot_examples)
    
    # Add extraction instructions
    prompt_parts.append("\n# EXTRACTION TASK")
    prompt_parts.append("Extract data from the document below according to the schema above.")
    prompt_parts.append("Remember: Return ONLY the JSON object, no explanations.")
    
    prompt = "\n".join(prompt_parts)
    
    # Generate schema hash for provenance
    schema_bytes = json.dumps(schema, sort_keys=True).encode()
    schema_hash = hashlib.sha256(schema_bytes).hexdigest()
    
    # Build metadata
    metadata = {
        "slug": slug,
        "schema": schema,
        "schema_sha256": schema_hash,
        "has_few_shot": bool(few_shot_examples),
        "schema_properties_count": len(schema.get("properties", {})),
        **meta  # Include loader metadata
    }
    
    return prompt, metadata