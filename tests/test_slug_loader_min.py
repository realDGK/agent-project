import os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = Path(os.getenv("DOC_TYPES_DIR", ROOT/"config/prompts/document_types"))

def _load_schema_from_slug(slug: str):
    d = DOC_DIR/slug
    ss = d/f"{slug}_ss.json"
    sa = d/f"{slug}_sa.json"
    base = {}
    if ss.exists():
        base = json.loads(ss.read_text(encoding="utf-8"))
    if sa.exists():
        add = json.loads(sa.read_text(encoding="utf-8"))
        if isinstance(base, dict) and isinstance(add, dict):
            base = base | add
    return base

def test_three_well_known_slugs_have_properties():
    for slug in ["purchase-sale-agreement-psa","letter-of-intent-loi","grant-deed"]:
        d = DOC_DIR/slug
        assert d.is_dir(), f"missing dir for {slug}"
        schema = _load_schema_from_slug(slug)
        assert isinstance(schema, dict) and "properties" in schema, f"schema missing properties for {slug}"
