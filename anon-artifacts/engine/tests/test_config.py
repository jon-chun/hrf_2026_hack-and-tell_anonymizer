import pytest

from anon3pass.config import load_config, load_terms


def test_defaults_load():
    cfg = load_config(None)
    assert cfg["pass2_libraries"]["ner"]["engine"] == "presidio_spacy"
    assert "~" not in cfg["paths"]["key_file"]


def test_override_merges(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("pass2_libraries:\n  ner:\n    score_threshold: 0.7\nentity_policy:\n  EMAIL: redact\n")
    cfg = load_config(str(p))
    assert cfg["pass2_libraries"]["ner"]["score_threshold"] == 0.7
    assert cfg["pass2_libraries"]["ner"]["engine"] == "presidio_spacy"  # untouched sibling kept
    assert cfg["entity_policy"]["EMAIL"] == "redact" and cfg["entity_policy"]["PERSON"] == "surrogate"


@pytest.mark.parametrize("body", [
    "entity_policy:\n  EMAIL: scramble\n",
    "entity_policy:\n  NOPE: redact\n",
    "pass3_agent_qa:\n  backend: gpt\n",
    "pass2_libraries:\n  ner:\n    engine: magic\n",
    "pass2_libraries:\n  secrets:\n    gitleaks: maybe\n",
    "pipeline:\n  fail_on: severe\n",
])
def test_invalid_values_raise(tmp_path, body):
    p = tmp_path / "c.yaml"
    p.write_text(body)
    with pytest.raises(ValueError):
        load_config(str(p))


def test_terms_missing_file_is_empty(tmp_path):
    cfg = load_config(None)
    cfg["paths"]["terms_file"] = str(tmp_path / "none.yaml")
    assert load_terms(cfg) == {"deny": [], "allow": []}


def test_terms_parsed(tmp_path):
    t = tmp_path / "terms.yaml"
    t.write_text("deny:\n  - {term: Jane Roe, entity: PERSON}\n  - Acme Widgets\nallow:\n  - Geneva\n")
    cfg = load_config(None)
    cfg["paths"]["terms_file"] = str(t)
    assert load_terms(cfg) == {
        "deny": [{"term": "Jane Roe", "entity": "PERSON"}, {"term": "Acme Widgets", "entity": "CUSTOM"}],
        "allow": ["Geneva"]}


def test_terms_bad_entity(tmp_path):
    t = tmp_path / "terms.yaml"
    t.write_text("deny:\n  - {term: X, entity: BOGUS}\n")
    cfg = load_config(None)
    cfg["paths"]["terms_file"] = str(t)
    with pytest.raises(ValueError):
        load_terms(cfg)
