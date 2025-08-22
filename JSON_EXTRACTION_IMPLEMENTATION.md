# JSON Extraction Implementation

## Overview
Successfully implemented a robust JSON extraction system with schema validation and repair loop, integrated with the enhanced schema loader.

## Components Implemented

### 1. JSON Schema Guard (`src/app/agents/json_extract.py`)
- **Auto-repair loop**: Automatically fixes invalid JSON responses (up to 3 attempts)
- **Schema validation**: Uses jsonschema to validate against document type schemas
- **Multi-provider support**: Works with Anthropic and OpenAI
- **Error recovery**: Detailed error messages for debugging

### 2. Gemini-specific Extractor (`src/app/agents/json_extract_gemini.py`)
- Optimized for Gemini AI (already configured in your system)
- Same repair loop and validation features
- Uses your existing GOOGLE_API_KEY

### 3. Extraction Handoff Service (`src/app/services/extractor_handoff.py`)
- **Prompt bundling**: Combines schema, few-shot examples, and instructions
- **Slug normalization**: Maps various input formats to correct slugs
- **Provenance tracking**: Generates SHA-256 hash for schema versioning
- **Metadata enrichment**: Includes all relevant metadata for audit trail

### 4. One-shot CLI Tools
- `scripts/extract_one.py`: Generic extractor (Anthropic/OpenAI)
- `scripts/extract_one_gemini.py`: Gemini-specific extractor
- Both save results with full provenance to `logs/`

### 5. Make Shortcuts
```bash
make extract-one slug=letter-of-intent-loi file=data/sample_loi.txt
make extract-gemini slug=purchase-sale-agreement-psa file=data/sample_psa.txt
```

## Usage Examples

### Basic Extraction
```bash
# Using Gemini (recommended for your setup)
python3 scripts/extract_one_gemini.py letter-of-intent-loi data/sample_loi.txt

# Using Anthropic/OpenAI
export ANTHROPIC_API_KEY=your-key
python3 scripts/extract_one.py purchase-sale-agreement-psa data/sample_psa.txt
```

### Environment Variables
```bash
# Gemini (already configured)
export GOOGLE_API_KEY=your-key
export GEMINI_MODEL=gemini-2.0-flash-exp  # or gemini-2.0-pro

# Anthropic
export ANTHROPIC_API_KEY=your-key
export ANTHROPIC_MODEL=claude-3-5-sonnet-latest

# OpenAI
export OPENAI_API_KEY=your-key
export OPENAI_MODEL=gpt-4o-mini

# Extraction settings
export EXTRACT_T=0.0              # Temperature (0.0 = deterministic)
export EXTRACT_MAX_TOKENS=4096    # Max tokens for response
```

## Output Format
Extractions are saved to `logs/extraction_<slug>_<timestamp>.json`:
```json
{
  "meta": {
    "slug": "letter-of-intent-loi",
    "schema_sha256": "a3f5d8e2...",
    "source_file": "data/sample_loi.txt",
    "properties_count": 12,
    "has_few_shot": true
  },
  "data": {
    "contract_name": "Letter of Intent",
    "effective_date": "2024-12-15",
    "parties": [...],
    // ... extracted fields
  }
}
```

## Features
✅ **Schema-first extraction**: Every extraction validated against schema
✅ **Auto-repair**: Automatically fixes malformed JSON responses
✅ **Provenance tracking**: SHA-256 hash ensures schema version consistency
✅ **Multi-model support**: Works with Gemini, Claude, and GPT
✅ **353 document types**: All schemas ready for extraction
✅ **Few-shot learning**: Uses examples when available

## Testing
```bash
# Run smoke test
python3 -c "from tests.test_e2e_prompt_bundle import test_bundle_psa_smoke; test_bundle_psa_smoke()"

# Test with sample document
python3 scripts/extract_one_gemini.py letter-of-intent-loi data/sample_loi.txt
```

## Next Steps
1. **Persist to PostgreSQL**: Wire extraction results to provenance tables
2. **PDF/DOC support**: Integrate with existing OCR pipeline
3. **Classifier integration**: Auto-detect document type before extraction
4. **Batch processing**: Process multiple documents in parallel
5. **HIL queue**: Route low-confidence extractions for human review

## Integration Points
- **Main API**: Update `main.py` to use `extract_json()` instead of raw Gemini calls
- **Provenance**: Store `meta['schema_sha256']` with each extraction
- **Conflict engine**: Use schema hash to detect when documents use different schemas
- **Audit trail**: Log all repair attempts for compliance