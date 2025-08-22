#!/usr/bin/env python3
"""
Batch Runner CLI for Document Type Validation
Validates all document types for schema compliance and MCP compatibility
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class DocumentTypeValidator:
    """Validates document type configurations"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.document_types_dir = base_path / "config" / "prompts" / "document_types"
        self.master_schema_path = base_path / "config" / "schema.json"
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'stats': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'duration': 0
            }
        }
    
    def load_master_schema(self) -> Dict:
        """Load the master schema"""
        try:
            with open(self.master_schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading master schema: {e}")
            return {}
    
    def validate_json_file(self, filepath: Path) -> Tuple[bool, str]:
        """Validate a JSON file is well-formed"""
        try:
            with open(filepath, 'r') as f:
                json.load(f)
            return True, "Valid JSON"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def validate_schema_additions(self, doc_dir: Path) -> Dict:
        """Validate schema_additions.json for a document type"""
        result = {
            'name': doc_dir.name,
            'path': str(doc_dir),
            'checks': {}
        }
        
        # Try both naming patterns
        schema_file = doc_dir / "schema_additions.json"
        if not schema_file.exists():
            # Try with numeric prefix pattern
            schema_files = list(doc_dir.glob("*_schema_additions.json"))
            if schema_files:
                schema_file = schema_files[0]
        
        # Check if file exists
        if not schema_file.exists():
            result['checks']['exists'] = False
            result['status'] = 'failed'
            result['message'] = "schema_additions.json not found"
            return result
        
        result['checks']['exists'] = True
        
        # Check if valid JSON
        is_valid, message = self.validate_json_file(schema_file)
        result['checks']['valid_json'] = is_valid
        
        if not is_valid:
            result['status'] = 'failed'
            result['message'] = message
            return result
        
        # Load and validate content
        try:
            with open(schema_file, 'r') as f:
                schema_additions = json.load(f)
            
            # Check if it's empty
            if not schema_additions:
                result['checks']['has_content'] = False
                result['status'] = 'warning'
                result['message'] = "schema_additions.json is empty"
                return result
            
            result['checks']['has_content'] = True
            
            # Check for proper structure (should be a dict with property definitions)
            if not isinstance(schema_additions, dict):
                result['checks']['proper_structure'] = False
                result['status'] = 'failed'
                result['message'] = "schema_additions must be an object/dict"
                return result
            
            result['checks']['proper_structure'] = True
            
            # Check each property definition
            invalid_props = []
            for prop_name, prop_def in schema_additions.items():
                if not isinstance(prop_def, dict):
                    invalid_props.append(f"{prop_name}: not an object")
                elif 'type' not in prop_def:
                    invalid_props.append(f"{prop_name}: missing 'type' field")
            
            if invalid_props:
                result['checks']['valid_properties'] = False
                result['status'] = 'failed'
                result['message'] = f"Invalid properties: {', '.join(invalid_props)}"
                return result
            
            result['checks']['valid_properties'] = True
            result['property_count'] = len(schema_additions)
            
        except Exception as e:
            result['status'] = 'failed'
            result['message'] = f"Error processing schema: {e}"
            return result
        
        result['status'] = 'passed'
        result['message'] = f"Valid schema with {len(schema_additions)} properties"
        return result
    
    def validate_few_shot_examples(self, doc_dir: Path) -> Dict:
        """Validate few_shot_examples.json for a document type"""
        result = {
            'name': doc_dir.name,
            'checks': {}
        }
        
        # Try both naming patterns
        examples_file = doc_dir / "few_shot_examples.json"
        if not examples_file.exists():
            # Try with numeric prefix pattern
            examples_files = list(doc_dir.glob("*_few_shot_examples.json"))
            if examples_files:
                examples_file = examples_files[0]
        
        # Check if file exists (optional file)
        if not examples_file.exists():
            result['checks']['exists'] = False
            result['status'] = 'info'
            result['message'] = "few_shot_examples.json not found (optional)"
            return result
        
        result['checks']['exists'] = True
        
        # Check if valid JSON
        is_valid, message = self.validate_json_file(examples_file)
        result['checks']['valid_json'] = is_valid
        
        if not is_valid:
            result['status'] = 'failed'
            result['message'] = f"few_shot_examples: {message}"
            return result
        
        # Load and validate content
        try:
            with open(examples_file, 'r') as f:
                examples = json.load(f)
            
            # Should be a list of examples
            if not isinstance(examples, list):
                result['checks']['is_array'] = False
                result['status'] = 'failed'
                result['message'] = "few_shot_examples must be an array"
                return result
            
            result['checks']['is_array'] = True
            result['example_count'] = len(examples)
            
            if len(examples) == 0:
                result['status'] = 'warning'
                result['message'] = "few_shot_examples is empty"
            else:
                result['status'] = 'passed'
                result['message'] = f"Valid with {len(examples)} examples"
                
        except Exception as e:
            result['status'] = 'failed'
            result['message'] = f"Error processing examples: {e}"
        
        return result
    
    def validate_specialist_schema(self, doc_dir: Path) -> Dict:
        """Validate specialist_schema.json for a document type"""
        result = {
            'name': doc_dir.name,
            'checks': {}
        }
        
        # Try both naming patterns
        schema_file = doc_dir / "specialist_schema.json"
        if not schema_file.exists():
            # Try with numeric prefix pattern
            schema_files = list(doc_dir.glob("*_specialist_schema.json"))
            if schema_files:
                schema_file = schema_files[0]
        
        # Check if file exists (optional file)
        if not schema_file.exists():
            result['checks']['exists'] = False
            result['status'] = 'info'
            result['message'] = "specialist_schema.json not found (optional)"
            return result
        
        result['checks']['exists'] = True
        
        # Check if valid JSON
        is_valid, message = self.validate_json_file(schema_file)
        result['checks']['valid_json'] = is_valid
        
        if not is_valid:
            result['status'] = 'failed'
            result['message'] = f"specialist_schema: {message}"
            return result
        
        result['status'] = 'passed'
        result['message'] = "Valid specialist schema"
        return result
    
    def validate_document_type(self, doc_dir: Path) -> Dict:
        """Validate a single document type directory"""
        results = {
            'directory': doc_dir.name,
            'path': str(doc_dir),
            'validations': {}
        }
        
        # Validate schema_additions (required)
        schema_result = self.validate_schema_additions(doc_dir)
        results['validations']['schema_additions'] = schema_result
        
        # Validate few_shot_examples (optional)
        examples_result = self.validate_few_shot_examples(doc_dir)
        results['validations']['few_shot_examples'] = examples_result
        
        # Validate specialist_schema (optional)
        specialist_result = self.validate_specialist_schema(doc_dir)
        results['validations']['specialist_schema'] = specialist_result
        
        # Determine overall status
        statuses = [v['status'] for v in results['validations'].values()]
        
        if 'failed' in statuses:
            results['overall_status'] = 'failed'
        elif 'warning' in statuses:
            results['overall_status'] = 'warning'
        else:
            results['overall_status'] = 'passed'
        
        return results
    
    def run_validation(self, doc_types: Optional[List[str]] = None, verbose: bool = False) -> Dict:
        """Run validation on all or specified document types"""
        start_time = time.time()
        
        # Get list of directories to validate
        if doc_types:
            dirs_to_validate = [
                d for d in self.document_types_dir.iterdir()
                if d.is_dir() and d.name in doc_types
            ]
        else:
            dirs_to_validate = [
                d for d in self.document_types_dir.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ]
        
        self.results['stats']['total'] = len(dirs_to_validate)
        
        print(f"Validating {len(dirs_to_validate)} document types...")
        print("=" * 60)
        
        for doc_dir in sorted(dirs_to_validate):
            if verbose:
                print(f"Validating: {doc_dir.name}...", end=" ")
            
            result = self.validate_document_type(doc_dir)
            
            if result['overall_status'] == 'failed':
                self.results['failed'].append(result)
                self.results['stats']['failed'] += 1
                if verbose:
                    print("❌ FAILED")
            elif result['overall_status'] == 'warning':
                self.results['warnings'].append(result)
                self.results['stats']['warnings'] += 1
                if verbose:
                    print("⚠️  WARNING")
            else:
                self.results['passed'].append(result)
                self.results['stats']['passed'] += 1
                if verbose:
                    print("✅ PASSED")
        
        self.results['stats']['duration'] = time.time() - start_time
        
        return self.results
    
    def print_summary(self):
        """Print validation summary"""
        stats = self.results['stats']
        
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total document types: {stats['total']}")
        print(f"  ✅ Passed:  {stats['passed']}")
        print(f"  ⚠️  Warnings: {stats['warnings']}")
        print(f"  ❌ Failed:  {stats['failed']}")
        print(f"Duration: {stats['duration']:.2f} seconds")
        
        # Show failed items
        if self.results['failed']:
            print("\n❌ FAILED VALIDATIONS:")
            for item in self.results['failed']:
                print(f"  - {item['directory']}:")
                for val_name, val_result in item['validations'].items():
                    if val_result['status'] == 'failed':
                        print(f"    • {val_name}: {val_result['message']}")
        
        # Show warnings
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for item in self.results['warnings']:
                print(f"  - {item['directory']}:")
                for val_name, val_result in item['validations'].items():
                    if val_result['status'] == 'warning':
                        print(f"    • {val_name}: {val_result['message']}")
        
        print("\n" + "=" * 60)
        
        # Return exit code
        return 0 if stats['failed'] == 0 else 1
    
    def save_report(self, output_file: Path):
        """Save detailed validation report to JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.results['stats'],
            'results': {
                'passed': self.results['passed'],
                'warnings': self.results['warnings'],
                'failed': self.results['failed']
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed report saved to: {output_file}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Batch runner for document type validation'
    )
    
    parser.add_argument(
        '--types',
        nargs='+',
        help='Specific document types to validate (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation progress'
    )
    
    parser.add_argument(
        '--report', '-r',
        type=str,
        help='Save detailed report to JSON file'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )
    
    args = parser.parse_args()
    
    # Get base path
    base_path = Path("/home/scott/agent-project")
    
    # Create validator
    validator = DocumentTypeValidator(base_path)
    
    # Run validation
    results = validator.run_validation(
        doc_types=args.types,
        verbose=args.verbose
    )
    
    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        validator.save_report(report_path)
    
    # Print summary and exit
    exit_code = validator.print_summary()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()