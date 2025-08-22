"""
Enhanced schema loader with additional features
"""
import os
import json
import hashlib
from typing import Dict, Tuple, Optional
from pathlib import Path

class SchemaLoader:
    """Enhanced schema loader with caching and validation"""
    
    def __init__(self, doc_types_dir: str = None):
        self.doc_types_dir = Path(doc_types_dir or os.getenv("DOC_TYPES_DIR", "config/prompts/document_types"))
        self._cache = {}
        
    def _deep_merge(self, a: dict, b: dict) -> dict:
        """Deep merge b into a"""
        for k, v in (b or {}).items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                self._deep_merge(a[k], v)
            else:
                a[k] = v
        return a
    
    def _read_json(self, path: Path) -> dict:
        """Read JSON with error context"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate it's a dict
                if not isinstance(data, dict):
                    raise ValueError(f"Expected dict, got {type(data).__name__}")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
    
    def _read_text(self, path: Path) -> str:
        """Read text file safely"""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    def _get_cache_key(self, slug: str, base_schema_path: Optional[str]) -> str:
        """Generate cache key for loaded schema"""
        return f"{slug}:{base_schema_path or 'default'}"
    
    def load_for_doc_type(
        self, 
        slug: str, 
        base_schema_path: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[Dict, str, Dict]:
        """
        Load schema for document type with caching
        
        Directory: <DOC_TYPES_DIR>/<slug>/
          - <slug>_ss.json  (Specialist Schema)    [optional]
          - <slug>_sa.json  (Schema Additions)     [optional]
          - <slug>_fse.txt  (Few Shot Examples)    [optional]
          
        Returns: (merged_schema, few_shot_text, metadata)
        """
        # Check cache first
        cache_key = self._get_cache_key(slug, base_schema_path)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Validate directory exists
        ddir = self.doc_types_dir / slug
        if not ddir.is_dir():
            raise FileNotFoundError(f"Doc type folder not found: {ddir}")
        
        # Define file paths
        spec_path = ddir / f"{slug}_ss.json"
        adds_path = ddir / f"{slug}_sa.json"
        fse_path = ddir / f"{slug}_fse.txt"
        
        # Check at least one schema file exists
        has_spec = spec_path.is_file()
        has_adds = adds_path.is_file()
        
        if not (has_spec or has_adds):
            raise FileNotFoundError(
                f"{slug}: expected {slug}_ss.json and/or {slug}_sa.json in {ddir}"
            )
        
        # Load base schema
        base_path = Path(base_schema_path or "schema.json")
        if base_path.exists():
            base = self._read_json(base_path)
        else:
            base = {}  # Start with empty if no base
        
        # Deep copy base
        merged = json.loads(json.dumps(base))
        
        # Merge specialist schema
        if has_spec:
            spec_data = self._read_json(spec_path)
            self._deep_merge(merged, spec_data)
        
        # Merge additions
        if has_adds:
            adds_data = self._read_json(adds_path)
            self._deep_merge(merged, adds_data)
        
        # Load few-shot examples
        few_shot_text = ""
        if fse_path.is_file():
            few_shot_text = self._read_text(fse_path)
        
        # Build metadata
        meta = {
            "slug": slug,
            "dir": str(ddir),
            "base": str(base_path),
            "specialist": str(spec_path) if has_spec else None,
            "additions": str(adds_path) if has_adds else None,
            "few_shot": str(fse_path) if fse_path.is_file() else None,
            "schema_hash": hashlib.md5(json.dumps(merged, sort_keys=True).encode()).hexdigest()[:8]
        }
        
        result = (merged, few_shot_text, meta)
        
        # Cache the result
        if use_cache:
            self._cache[cache_key] = result
        
        return result
    
    def validate_schema(self, schema: dict, slug: str) -> list:
        """Validate schema structure and return issues"""
        issues = []
        
        # Check for required top-level fields
        if "properties" not in schema:
            issues.append(f"{slug}: missing 'properties' field")
        
        # Check for discovered_entities field (safety net)
        if "properties" in schema and "discovered_entities" not in schema["properties"]:
            issues.append(f"{slug}: missing 'discovered_entities' safety net field")
        
        # Check for at least one required field
        if "required" in schema and not schema["required"]:
            issues.append(f"{slug}: 'required' array is empty")
        
        return issues
    
    def get_all_slugs(self) -> list:
        """Get all available document type slugs"""
        return sorted([
            d.name for d in self.doc_types_dir.iterdir() 
            if d.is_dir() and not d.name.startswith('.')
        ])

# Backwards compatible function
def load_for_doc_type(slug: str, base_schema_path: Optional[str] = None) -> Tuple[Dict, str, Dict]:
    """Backwards compatible wrapper"""
    loader = SchemaLoader()
    return loader.load_for_doc_type(slug, base_schema_path)