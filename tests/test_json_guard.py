"""
Unit tests for JSON guard functionality
"""
import pytest
import json
from src.app.agents.json_extract import _first_json_blob, _validate

def test_first_json_blob_basic():
    txt = "noise {\"a\": 1, \"b\": {\"c\":2}} trailing"
    blob = _first_json_blob(txt)
    assert blob and blob.startswith("{") and blob.endswith("}")

def test_validate_ok_and_fail():
    schema = {"type":"object","properties":{"foo":{"type":"string"}}, "required":["foo"]}
    ok, why = _validate({"foo":"bar"}, schema)
    assert ok and why == ""
    ok2, why2 = _validate({}, schema)
    assert not ok2 and "foo" in why2
