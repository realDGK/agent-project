import os, sys, json, glob, difflib, hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from src.app.agents.json_extract import extract_json

ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = Path(os.getenv("DOC_TYPES_DIR", ROOT/"config/prompts/document_types"))
PREPROMPT_PATH = Path(os.getenv("CLASSIFIER_AGENT_PREPROMPT", ROOT/"config/prompts/Pre_prompt.txt"))

def _slugify(s: str) -> str:
    import re
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def _resolve_slug(label_or_slug: str) -> str:
    want = _slugify(label_or_slug)
    # exact dir match
    if (DOC_DIR/want).is_dir():
        return want
    # try mapping file if present
    map_path = ROOT/"directory_name_mapping.json"
    if map_path.exists():
        try:
            m = json.loads(map_path.read_text(encoding="utf-8"))
            mappings = (m.get("mappings") or {}) | {v:k for v,k in (m.get("reverse_mappings") or {}).items()}
            if label_or_slug in mappings:
                s = mappings[label_or_slug]
                s = s if (DOC_DIR/s).is_dir() else want
                if (DOC_DIR/s).is_dir():
                    return s
        except Exception:
            pass
    # fuzzy dir match
    choices = [p.name for p in DOC_DIR.iterdir() if p.is_dir()]
    best = difflib.get_close_matches(want, choices, n=1, cutoff=0.72)
    if best:
        return best[0]
    raise SystemExit(f"Could not resolve slug for: {label_or_slug}")

def _load_schema(slug: str) -> Dict[str, Any]:
    d = DOC_DIR/slug
    ss = next(iter(glob.glob(str(d/f"{slug}_ss.json"))), None)
    sa = next(iter(glob.glob(str(d/f"{slug}_sa.json"))), None)
    base: Dict[str, Any] = {}
    if ss:
        base = json.loads(Path(ss).read_text(encoding="utf-8"))
    if sa and Path(sa).exists():
        add = json.loads(Path(sa).read_text(encoding="utf-8"))
        # small deep-merge: only for dicts
        def merge(a: Any, b: Any) -> Any:
            if isinstance(a, dict) and isinstance(b, dict):
                out = dict(a)
                for k, v in b.items():
                    out[k] = merge(a.get(k), v)
                return out
            return b if b is not None else a
        base = merge(base, add)
    if not isinstance(base, dict) or "properties" not in base:
        raise SystemExit(f"Schema invalid for {slug}: missing 'properties'")
    return base

def _load_few_shot(slug: str) -> str:
    p = DOC_DIR/slug/f"{slug}_fse.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def _build_prompt(slug: str, schema: Dict[str, Any], few_shot: str, preprompt: str) -> str:
    schema_txt = json.dumps(schema, ensure_ascii=False, indent=2)
    prompt = (
        f"{preprompt.strip()}\n\n"
        f"# DOCUMENT TYPE: {slug}\n"
        f"# FEW-SHOT EXAMPLES\n{few_shot.strip()}\n\n"
        f"# STRICT JSON SCHEMA (Draft 2020-12)\n{schema_txt}\n"
        "You must return ONLY one JSON object that strictly validates against the schema."
    )
    return prompt

def _schema_sha(schema: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/extract_one.py <slug-or-label> <path-to-text-file> [--online]")
        sys.exit(2)

    slug = _resolve_slug(sys.argv[1])
    text_path = Path(sys.argv[2])
    online = "--online" in sys.argv[3:]

    if not text_path.is_file():
        print(f"File not found: {text_path}")
        sys.exit(2)

    schema = _load_schema(slug)
    few = _load_few_shot(slug)
    pre = PREPROMPT_PATH.read_text(encoding="utf-8")
    prompt = _build_prompt(slug, schema, few, pre)

    doc = text_path.read_text(encoding="utf-8", errors="ignore").strip()
    prompt = f"{prompt}\n\n# DOCUMENT CONTENT (verbatim)\n{doc}"

    os.makedirs("logs", exist_ok=True)
    (Path("logs")/f"prompt_{slug}.txt").write_text(prompt, encoding="utf-8")

    meta = {"slug": slug, "schema_sha256": _schema_sha(schema)}
    if not online or os.getenv("EXTRACT_PROVIDER","offline").lower() == "offline":
        print(f"DRY RUN ✓  Prompt saved → logs/prompt_{slug}.txt")
        print("Set EXTRACT_PROVIDER=anthropic (or openai) and pass --online to perform extraction.")
        return

    from src.app.agents.json_extract import extract_json
    obj = extract_json(prompt, schema)
    out_path = Path("logs")/f"extraction_{slug}.json"
    out_path.write_text(json.dumps({"meta": meta, "data": obj}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Extraction OK → {out_path}")

if __name__ == "__main__":
    main()