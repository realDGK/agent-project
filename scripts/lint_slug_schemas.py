#!/usr/bin/env python3
"""
Linter for document type schemas with registry generation
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib

class SchemaLinter:
    def __init__(self, doc_types_dir: str = "config/prompts/document_types"):
        self.doc_types_dir = Path(doc_types_dir)
        self.issues = []
        self.registry = {}
        
    def lint_json(self, path: Path) -> dict:
        """Lint and load JSON file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    self.issues.append(f"{path}: Not a JSON object")
                    return {}
                return data
        except json.JSONDecodeError as e:
            self.issues.append(f"{path}: Invalid JSON - {e}")
            return {}
        except FileNotFoundError:
            return {}
    
    def check_naming(self, slug: str, ddir: Path) -> bool:
        """Check file naming conventions"""
        expected_files = {
            f"{slug}_ss.json": False,  # Specialist Schema
            f"{slug}_sa.json": False,  # Schema Additions
            f"{slug}_fse.txt": False   # Few-Shot Examples
        }
        
        found_any_schema = False
        for fname, required in expected_files.items():
            fpath = ddir / fname
            if fpath.exists():
                if fname.endswith(".json"):
                    found_any_schema = True
                    
        if not found_any_schema:
            self.issues.append(f"{slug}: Missing both _ss.json and _sa.json")
            return False
            
        # Check for old naming patterns
        old_patterns = [
            "schema.json", "few_shot.txt", "additions.json",
            "*.schema.json", "*.few_shot.txt"
        ]
        for pattern in old_patterns:
            if list(ddir.glob(pattern)):
                self.issues.append(f"{slug}: Found old naming pattern: {pattern}")
                
        return True
    
    def validate_schema_structure(self, schema: dict, slug: str, file_type: str) -> None:
        """Validate schema structure"""
        if file_type == "_ss":  # Specialist Schema
            # Should have title, type, properties
            if "title" not in schema:
                self.issues.append(f"{slug}_ss.json: Missing 'title' field")
            if "type" not in schema or schema["type"] != "object":
                self.issues.append(f"{slug}_ss.json: Should have type='object'")
            if "properties" not in schema:
                self.issues.append(f"{slug}_ss.json: Missing 'properties' field")
            else:
                # Check for common required fields
                props = schema["properties"]
                recommended = ["contract_name", "effective_date", "parties"]
                missing = [f for f in recommended if f not in props]
                if missing:
                    self.issues.append(f"{slug}_ss.json: Consider adding: {', '.join(missing)}")
                    
        elif file_type == "_sa":  # Schema Additions
            # Should only contain property additions/overrides
            if "title" in schema or "type" in schema:
                self.issues.append(f"{slug}_sa.json: Should not redefine title/type (additions only)")
    
    def validate_few_shot(self, fse_path: Path, slug: str) -> None:
        """Validate few-shot examples format"""
        if not fse_path.exists():
            return
            
        try:
            with open(fse_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check for basic structure
            if "**INPUT" not in content:
                self.issues.append(f"{slug}_fse.txt: Missing **INPUT section")
            if "**JSON OUTPUT" not in content or "**OUTPUT" not in content:
                self.issues.append(f"{slug}_fse.txt: Missing **OUTPUT section")
                
            # Try to extract and validate JSON
            if "**JSON OUTPUT" in content:
                json_start = content.find("{", content.find("**JSON OUTPUT"))
                json_end = content.rfind("}") + 1
                if json_start > 0 and json_end > json_start:
                    try:
                        json_str = content[json_start:json_end]
                        example = json.loads(json_str)
                        if not isinstance(example, dict):
                            self.issues.append(f"{slug}_fse.txt: Example JSON is not an object")
                    except json.JSONDecodeError:
                        self.issues.append(f"{slug}_fse.txt: Invalid JSON in example")
                        
        except Exception as e:
            self.issues.append(f"{slug}_fse.txt: Error reading file - {e}")
    
    def generate_hash(self, schema: dict) -> str:
        """Generate consistent hash for schema"""
        return hashlib.sha256(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()[:8]
    
    def lint_slug(self, slug: str) -> bool:
        """Lint a single document type"""
        ddir = self.doc_types_dir / slug
        
        if not ddir.is_dir():
            self.issues.append(f"{slug}: Directory not found")
            return False
            
        # Check naming
        if not self.check_naming(slug, ddir):
            return False
            
        # Load and validate schemas
        ss_path = ddir / f"{slug}_ss.json"
        sa_path = ddir / f"{slug}_sa.json"
        fse_path = ddir / f"{slug}_fse.txt"
        
        has_specialist = False
        has_additions = False
        
        if ss_path.exists():
            schema = self.lint_json(ss_path)
            if schema:
                has_specialist = True
                self.validate_schema_structure(schema, slug, "_ss")
                
        if sa_path.exists():
            additions = self.lint_json(sa_path)
            if additions:
                has_additions = True
                self.validate_schema_structure(additions, slug, "_sa")
                
        # Validate few-shot examples
        self.validate_few_shot(fse_path, slug)
        
        # Add to registry if valid
        if has_specialist or has_additions:
            # Merge schemas for hash
            merged = {}
            if has_specialist:
                merged.update(schema)
            if has_additions:
                # Deep merge additions
                for k, v in additions.items():
                    if k in merged and isinstance(v, dict) and isinstance(merged[k], dict):
                        merged[k].update(v)
                    else:
                        merged[k] = v
                        
            self.registry[slug] = {
                "path": str(ddir),
                "has_specialist": has_specialist,
                "has_additions": has_additions,
                "has_few_shot": fse_path.exists(),
                "hash": self.generate_hash(merged),
                "properties_count": len(merged.get("properties", {}))
            }
            return True
            
        return False
    
    def run(self) -> Tuple[List[str], Dict]:
        """Run linter on all document types"""
        slugs = sorted([
            d.name for d in self.doc_types_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])
        
        print(f"Linting {len(slugs)} document types...")
        valid_count = 0
        
        for slug in slugs:
            if self.lint_slug(slug):
                valid_count += 1
                print(f"  ✓ {slug}")
            else:
                print(f"  ✗ {slug}")
                
        print(f"\nResults: {valid_count}/{len(slugs)} valid")
        
        if self.issues:
            print(f"\n⚠ Found {len(self.issues)} issues:")
            for issue in self.issues[:20]:  # Show first 20
                print(f"  - {issue}")
            if len(self.issues) > 20:
                print(f"  ... and {len(self.issues) - 20} more")
                
        return self.issues, self.registry
    
    def save_registry(self, output_path: str = "config/prompts/document_types/registry.json"):
        """Save registry to JSON file"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2, sort_keys=True)
        print(f"\n✓ Registry saved to {output_path}")
        print(f"  Total schemas: {len(self.registry)}")
        print(f"  With specialist: {sum(1 for v in self.registry.values() if v['has_specialist'])}")
        print(f"  With additions: {sum(1 for v in self.registry.values() if v['has_additions'])}")
        print(f"  With few-shot: {sum(1 for v in self.registry.values() if v['has_few_shot'])}")

def main():
    linter = SchemaLinter()
    issues, registry = linter.run()
    
    if registry:
        linter.save_registry()
        
    # Exit with error if issues found
    sys.exit(1 if issues else 0)

if __name__ == "__main__":
    main()