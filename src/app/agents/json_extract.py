import os, json, time, re
from typing import Any, Dict, Tuple

try:
    import jsonschema
except Exception as e:
    raise SystemExit("Please add 'jsonschema>=4.22.0' to requirements.txt") from e

JSON_BLOCK_RE = re.compile(r"\{(?:[^{}]|(?R))*\}", re.S)

def _first_json_blob(text: str) -> str | None:
    m = JSON_BLOCK_RE.search(text or "")
    return m.group(0) if m else None

def _validate(obj: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        jsonschema.Draft202012Validator(schema).validate(obj)
        return True, ""
    except jsonschema.exceptions.ValidationError as e:
        path = "$." + ".".join(map(str, list(e.path)))
        return False, f"{path}: {e.message}"

def _load_openai():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

def _load_anthropic():
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key)

def _call_model(prompt: str, provider: str = "anthropic", model: str | None = None) -> str:
    provider = (provider or "anthropic").lower()
    if provider == "openai":
        client = _load_openai()
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"system","content":prompt}],
            temperature=float(os.getenv("EXTRACT_T", "0.0")),
        )
        return resp.choices[0].message.content
    else:
        client = _load_anthropic()
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        resp = client.messages.create(
            model=model,
            max_tokens=int(os.getenv("EXTRACT_MAX_TOKENS","4096")),
            temperature=float(os.getenv("EXTRACT_T", "0.0")),
            system=prompt,
            messages=[{"role":"user","content":"Return ONLY the JSON object."}],
        )
        return "".join(getattr(part, "text", "") for part in resp.content)

def extract_json(prompt: str, schema: Dict[str, Any], max_tries: int = 3) -> Dict[str, Any]:
    """
    Calls the model, extracts first JSON block, and validates against `schema`.
    Retries with a repair instruction up to `max_tries`. Returns a validated object.
    """
    provider = os.getenv("EXTRACT_PROVIDER", "anthropic")
    model = os.getenv("EXTRACT_MODEL")
    last_err = None
    reply = ""

    for attempt in range(1, max_tries+1):
        if attempt == 1:
            reply = _call_model(prompt, provider, model)
        else:
            repaired_prompt = (
                f"{prompt}\n\n# REPAIR CONTEXT\n"
                f"Prior response:\n{reply}\n\n"
                "Your previous response was invalid. "
                "Return ONLY a strictly valid JSON object that conforms to the schema above."
            )
            reply = _call_model(repaired_prompt, provider, model)

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