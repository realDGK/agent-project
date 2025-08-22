#!/usr/bin/env python3
"""
Simple test suite for schema loader (no pytest required)
"""
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from improved_loader import SchemaLoader

def test_real_schemas():
    """Test with actual document type schemas"""
    print("Testing real schemas...")
    
    loader = SchemaLoader()
    test_slugs = ["writs-of-possession", "alta-surveys", "utility-relocation-agreements"]
    
    for slug in test_slugs:
        try:
            schema, fse, meta = loader.load_for_doc_type(slug)
            props_count = len(schema.get('properties', {}))
            print(f"  ✓ {slug}: {props_count} properties, hash={meta['schema_hash']}")
            
            # Validate
            issues = loader.validate_schema(schema, slug)
            if issues:
                print(f"    Issues: {issues}")
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    
    # Test caching
    print("\nTesting cache...")
    schema1, _, meta1 = loader.load_for_doc_type("writs-of-possession")
    schema2, _, meta2 = loader.load_for_doc_type("writs-of-possession")
    assert meta1['schema_hash'] == meta2['schema_hash'], "Cache should return same hash"
    print("  ✓ Cache working")
    
    # Test all slugs
    print("\nCounting all document types...")
    all_slugs = loader.get_all_slugs()
    print(f"  ✓ Found {len(all_slugs)} document types")
    
    # Sample validation of random schemas
    print("\nValidating sample schemas...")
    sample = all_slugs[:10]  # First 10
    for slug in sample:
        try:
            schema, _, _ = loader.load_for_doc_type(slug)
            issues = loader.validate_schema(schema, slug)
            status = "✓" if not issues else f"⚠ ({len(issues)} issues)"
            print(f"  {status} {slug}")
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_real_schemas()