"""
JSON extraction with Gemini AI and schema validation
"""
import os, json, time
from typing import Any, Dict, Tuple

try:
    import jsonschema
except Exception as e:
    raise SystemExit("Please add 'jsonschema>=4.22.0' to requirements.txt") from e

try:
    import google.generativeai as genai
except ImportError:
    raise SystemExit("Please install google-generativeai") from None

def _call_gemini(prompt: str, model_name: str = None) -> str:
    """Call Gemini model"""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
    
    genai.configure(api_key=api_key)
    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": float(os.getenv("EXTRACT_T", "0.0")),
            "max_output_tokens": int(os.getenv("EXTRACT_MAX_TOKENS", "4096")),
        }
    )
    
    response = model.generate_content(prompt)
    return response.text

def _first_json_blob(text: str) -> str | None:
    """Extract first JSON object from text"""
    if not text:
        return None
    
    # Try to find JSON object boundaries
    start = text.find('{')
    if start == -1:
        return None
    
    # Simple bracket counting approach
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
    
    return None

def _validate(obj: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate object against schema"""
    try:
        jsonschema.Draft202012Validator(schema).validate(obj)
        return True, ""
    except jsonschema.exceptions.ValidationError as e:
        path = "$." + ".".join(map(str, list(e.path)))
        return False, f"{path}: {e.message}"

def extract_json(prompt: str, schema: Dict[str, Any], max_tries: int = 3) -> Dict[str, Any]:
    """
    Calls Gemini, tries to parse JSON, and repairs if needed against schema.
    Returns a validated JSON object or raises RuntimeError.
    """
    last_err = None
    reply = ""
    
    full_prompt = prompt + "\n\nReturn ONLY a valid JSON object that conforms to the provided schema."

    for attempt in range(1, max_tries+1):
        if attempt == 1:
            reply = _call_gemini(full_prompt)
        else:
            # Instruct repair on the prior reply
            repair_prompt = (
                f"{prompt}\n\n"
                f"# REPAIR CONTEXT\n"
                f"Your previous response was invalid. Error: {last_err}\n"
                f"Previous response: {reply}\n\n"
                f"Return ONLY a strictly valid JSON object that conforms to the schema."
            )
            reply = _call_gemini(repair_prompt)

        blob = _first_json_blob(reply)
        if not blob:
            last_err = f"no JSON detected in model reply (len={len(reply)})"
            continue

        try:
            obj = json.loads(blob)
        except Exception as e:
            last_err = f"json.loads failed: {e}"
            continue

        ok, why = _validate(obj, schema)
        if ok:
            return obj
        last_err = f"schema validation failed: {why}"
        time.sleep(0.4)

    raise RuntimeError(last_err or "failed to extract JSON")