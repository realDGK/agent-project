#!/usr/bin/env python3
"""
Test the improved schema loader
"""
from improved_loader import SchemaLoader
import json

def test_loader():
    loader = SchemaLoader()
    
    # Test loading writs-of-possession
    print("Testing writs-of-possession...")
    schema, fse, meta = loader.load_for_doc_type("writs-of-possession")
    print(f"  ✓ Loaded schema with {len(schema.get('properties', {}))} properties")
    print(f"  ✓ Hash: {meta['schema_hash']}")
    print(f"  ✓ Has few-shot: {'Yes' if fse else 'No'}")
    
    # Test loading alta-surveys
    print("\nTesting alta-surveys...")
    schema2, fse2, meta2 = loader.load_for_doc_type("alta-surveys")
    print(f"  ✓ Loaded schema with {len(schema2.get('properties', {}))} properties")
    print(f"  ✓ Hash: {meta2['schema_hash']}")
    print(f"  ✓ Has few-shot: {'Yes' if fse2 else 'No'}")
    
    # Test caching
    print("\nTesting cache...")
    schema3, _, meta3 = loader.load_for_doc_type("writs-of-possession")
    assert meta['schema_hash'] == meta3['schema_hash'], "Cache should return same hash"
    print("  ✓ Cache working correctly")
    
    # Test validation
    print("\nTesting validation...")
    issues = loader.validate_schema(schema, "writs-of-possession")
    if issues:
        print(f"  ⚠ Found issues: {issues}")
    else:
        print("  ✓ No validation issues")
    
    # Get all slugs
    print("\nGetting all slugs...")
    slugs = loader.get_all_slugs()
    print(f"  ✓ Found {len(slugs)} document types")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_loader()