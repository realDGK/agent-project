#!/usr/bin/env python3
"""
Comprehensive test suite for schema loader
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from improved_loader import SchemaLoader

class TestSchemaLoader:
    @pytest.fixture
    def temp_doc_dir(self):
        """Create temporary document type directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def loader(self, temp_doc_dir):
        """Create loader with temp directory"""
        return SchemaLoader(str(temp_doc_dir))
    
    def create_test_schema(self, temp_dir: Path, slug: str, 
                          has_specialist=True, has_additions=True, has_fse=True):
        """Create test schema files"""
        slug_dir = temp_dir / slug
        slug_dir.mkdir(parents=True)
        
        if has_specialist:
            specialist = {
                "title": f"{slug} Schema",
                "type": "object",
                "properties": {
                    "contract_name": {"type": "string"},
                    "effective_date": {"type": "string", "format": "date"}
                },
                "required": ["contract_name"]
            }
            with open(slug_dir / f"{slug}_ss.json", "w") as f:
                json.dump(specialist, f)
        
        if has_additions:
            additions = {
                "properties": {
                    "additional_field": {"type": "string"}
                }
            }
            with open(slug_dir / f"{slug}_sa.json", "w") as f:
                json.dump(additions, f)
        
        if has_fse:
            fse = """**INPUT DOCUMENT TEXT:**
Test document
**JSON OUTPUT:**
{"contract_name": "Test"}"""
            with open(slug_dir / f"{slug}_fse.txt", "w") as f:
                f.write(fse)
    
    def test_load_basic_schema(self, loader, temp_doc_dir):
        """Test loading a basic schema"""
        self.create_test_schema(temp_doc_dir, "test-doc")
        
        schema, fse, meta = loader.load_for_doc_type("test-doc")
        
        assert "properties" in schema
        assert "contract_name" in schema["properties"]
        assert "additional_field" in schema["properties"]  # From additions
        assert fse != ""
        assert meta["slug"] == "test-doc"
        assert meta["has_specialist"] is not None
    
    def test_specialist_only(self, loader, temp_doc_dir):
        """Test loading with only specialist schema"""
        self.create_test_schema(temp_doc_dir, "specialist-only", 
                              has_additions=False, has_fse=False)
        
        schema, fse, meta = loader.load_for_doc_type("specialist-only")
        
        assert "contract_name" in schema["properties"]
        assert "additional_field" not in schema["properties"]
        assert fse == ""
    
    def test_additions_only(self, loader, temp_doc_dir):
        """Test loading with only additions"""
        self.create_test_schema(temp_doc_dir, "additions-only",
                              has_specialist=False, has_fse=False)
        
        schema, fse, meta = loader.load_for_doc_type("additions-only")
        
        assert "additional_field" in schema["properties"]
        assert meta["specialist"] is None
    
    def test_missing_directory(self, loader):
        """Test error on missing directory"""
        with pytest.raises(FileNotFoundError, match="Doc type folder not found"):
            loader.load_for_doc_type("non-existent")
    
    def test_missing_schemas(self, loader, temp_doc_dir):
        """Test error when no schema files exist"""
        slug_dir = temp_doc_dir / "empty-doc"
        slug_dir.mkdir()
        
        with pytest.raises(FileNotFoundError, match="expected.*_ss.json and/or.*_sa.json"):
            loader.load_for_doc_type("empty-doc")
    
    def test_caching(self, loader, temp_doc_dir):
        """Test schema caching"""
        self.create_test_schema(temp_doc_dir, "cached-doc")
        
        # First load
        schema1, _, meta1 = loader.load_for_doc_type("cached-doc")
        
        # Modify file on disk
        slug_dir = temp_doc_dir / "cached-doc"
        with open(slug_dir / f"cached-doc_ss.json", "w") as f:
            json.dump({"properties": {"modified": {"type": "string"}}}, f)
        
        # Second load should come from cache
        schema2, _, meta2 = loader.load_for_doc_type("cached-doc")
        
        assert schema1 == schema2
        assert meta1["schema_hash"] == meta2["schema_hash"]
        
        # Load without cache should get new version
        schema3, _, meta3 = loader.load_for_doc_type("cached-doc", use_cache=False)
        assert "modified" in schema3["properties"]
    
    def test_deep_merge(self, loader, temp_doc_dir):
        """Test deep merging of schemas"""
        slug_dir = temp_doc_dir / "merge-test"
        slug_dir.mkdir()
        
        specialist = {
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "field1": {"type": "string"}
                    }
                }
            }
        }
        
        additions = {
            "properties": {
                "nested": {
                    "properties": {
                        "field2": {"type": "number"}
                    }
                }
            }
        }
        
        with open(slug_dir / "merge-test_ss.json", "w") as f:
            json.dump(specialist, f)
        with open(slug_dir / "merge-test_sa.json", "w") as f:
            json.dump(additions, f)
        
        schema, _, _ = loader.load_for_doc_type("merge-test")
        
        # Both fields should be present after merge
        assert "field1" in schema["properties"]["nested"]["properties"]
        assert "field2" in schema["properties"]["nested"]["properties"]
    
    def test_validation(self, loader, temp_doc_dir):
        """Test schema validation"""
        # Valid schema
        self.create_test_schema(temp_doc_dir, "valid-doc")
        schema, _, _ = loader.load_for_doc_type("valid-doc")
        issues = loader.validate_schema(schema, "valid-doc")
        
        # Only issue should be missing discovered_entities
        assert len(issues) == 1
        assert "discovered_entities" in issues[0]
        
        # Invalid schema - no properties
        invalid_schema = {"type": "object"}
        issues = loader.validate_schema(invalid_schema, "invalid")
        assert any("missing 'properties'" in i for i in issues)
    
    def test_get_all_slugs(self, loader, temp_doc_dir):
        """Test getting all document type slugs"""
        self.create_test_schema(temp_doc_dir, "doc1")
        self.create_test_schema(temp_doc_dir, "doc2")
        self.create_test_schema(temp_doc_dir, "doc3")
        
        # Create hidden directory (should be ignored)
        (temp_doc_dir / ".hidden").mkdir()
        
        slugs = loader.get_all_slugs()
        
        assert slugs == ["doc1", "doc2", "doc3"]
    
    def test_invalid_json(self, loader, temp_doc_dir):
        """Test handling of invalid JSON"""
        slug_dir = temp_doc_dir / "bad-json"
        slug_dir.mkdir()
        
        with open(slug_dir / "bad-json_ss.json", "w") as f:
            f.write("{invalid json}")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load_for_doc_type("bad-json")
    
    def test_hash_consistency(self, loader, temp_doc_dir):
        """Test that schema hash is consistent"""
        self.create_test_schema(temp_doc_dir, "hash-test")
        
        _, _, meta1 = loader.load_for_doc_type("hash-test")
        loader._cache.clear()  # Clear cache
        _, _, meta2 = loader.load_for_doc_type("hash-test")
        
        assert meta1["schema_hash"] == meta2["schema_hash"]

def test_real_schemas():
    """Test with actual document type schemas if available"""
    real_dir = Path("config/prompts/document_types")
    if not real_dir.exists():
        pytest.skip("Real document types directory not found")
    
    loader = SchemaLoader(str(real_dir))
    
    # Test a few known document types
    test_slugs = ["writs-of-possession", "alta-surveys", "utility-relocation-agreements"]
    
    for slug in test_slugs:
        if (real_dir / slug).exists():
            schema, fse, meta = loader.load_for_doc_type(slug)
            assert "properties" in schema
            assert meta["slug"] == slug
            print(f"✓ {slug}: {len(schema.get('properties', {}))} properties")

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])