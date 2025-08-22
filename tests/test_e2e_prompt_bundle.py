from src.app.services.extractor_handoff import build_prompt_bundle

def test_bundle_psa_smoke():
    prompt, meta = build_prompt_bundle("purchase-sale-agreement-psa")
    assert meta["slug"] == "purchase-sale-agreement-psa"
    assert isinstance(meta["schema"], dict)
    assert "properties" in meta["schema"]