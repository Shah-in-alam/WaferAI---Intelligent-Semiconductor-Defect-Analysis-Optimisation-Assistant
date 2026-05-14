from src.analyzer import DefectAnalysis, WaferAnalyzer


def test_fallback_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    analyzer = WaferAnalyzer(api_key=None)
    assert analyzer.client is None

    result = analyzer.analyze(
        {
            "defect_pattern": "Scratch",
            "model_confidence": 92.0,
            "defect_density": 4.5,
            "location": "Centre",
            "width": 100,
            "height": 100,
        }
    )
    assert isinstance(result, DefectAnalysis)
    assert result.defect_type == "Scratch"
    assert result.severity in {"Low", "Medium", "High", "Critical"}
    assert result.root_causes


def test_fallback_unknown_class_resolves_to_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    analyzer = WaferAnalyzer(api_key=None)
    result = analyzer.analyze({"defect_pattern": "NotAClass"})
    assert result.defect_type == "None"


def test_to_markdown_includes_all_sections(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    analyzer = WaferAnalyzer(api_key=None)
    result = analyzer.analyze({"defect_pattern": "Center"})
    md = result.to_markdown()
    for section in [
        "Defect Analysis",
        "Severity",
        "Root Causes",
        "Immediate Actions",
        "Process Improvements",
        "Quality Impact",
    ]:
        assert section in md


def test_chat_without_api_returns_helpful_message(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    analyzer = WaferAnalyzer(api_key=None)
    response = analyzer.chat_followup("Why is yield dropping?")
    assert "API key" in response or "first" in response.lower()
