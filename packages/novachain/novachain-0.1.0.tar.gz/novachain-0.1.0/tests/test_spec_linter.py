from agents_boot.tools.spec_linter import validate_spec

def test_linter_catches_missing_sections():
    issues = validate_spec("Just a random doc")
    assert "spec.missing_prd_keyword" in issues
    assert "spec.missing_api_section" in issues
    assert "spec.missing_acceptance_tests" in issues

def test_linter_accepts_minimal_valid_spec():
    spec = "PRD v0.1: API routes, acceptance tests"
    assert validate_spec(spec) == []
