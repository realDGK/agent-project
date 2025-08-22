#!/usr/bin/env python3
"""
Extract data from a document using Gemini AI
"""
import os, sys, json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.services.extractor_handoff import build_prompt_bundle
from src.app.agents.json_extract_gemini import extract_json

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/extract_one_gemini.py <slug-or-label> <path-to-text-file>")
        sys.exit(2)

    slug_or_label, path = sys.argv[1], sys.argv[2]
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(2)

    print(f"Loading document: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()

    print(f"Building prompt bundle for: {slug_or_label}")
    prompt, meta = build_prompt_bundle(slug_or_label)
    
    # Append the document content
    prompt = f"{prompt}\n\n# DOCUMENT CONTENT (verbatim, may be noisy)\n{text}"

    print(f"Extracting with schema: {meta['slug']} ({meta['schema_properties_count']} properties)")
    try:
        obj = extract_json(prompt, meta["schema"])
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        sys.exit(1)
    
    # Save results
    os.makedirs("logs", exist_ok=True)
    timestamp = Path(path).stem
    out_path = f"logs/extraction_{meta['slug']}_{timestamp}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "slug": meta["slug"],
                "schema_sha256": meta["schema_sha256"],
                "source_file": path,
                "properties_count": meta["schema_properties_count"],
                "has_few_shot": meta["has_few_shot"]
            },
            "data": obj
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Extraction OK → {out_path}")
    
    # Show sample of extracted data
    print("\nExtracted fields:")
    for key in list(obj.keys())[:5]:
        value = obj[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  - {key}: {value}")
    if len(obj) > 5:
        print(f"  ... and {len(obj) - 5} more fields")

if __name__ == "__main__":
    main()