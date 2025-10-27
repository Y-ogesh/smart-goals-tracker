import os
import json
import importlib
import types

# --- tiny helper to build an OpenAI-like response object ---
def _resp_with_text(text: str):
    class _Msg:  # mimics openai msg object
        def __init__(self, content): self.content = content
    class _Choice:
        def __init__(self, content): self.message = _Msg(content)
    class _Resp:
        def __init__(self, content): self.choices = [_Choice(content)]
    return _Resp(text)

def test_generate_plan_mock(monkeypatch):
    # Ensure import won't fail on missing key
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Import module under test
    gpt = importlib.import_module("gpt")

    # Patch ONLY the network call
    def fake_create(model, messages, temperature):
        # Return a valid JSON list string expected by generate_plan
        content = json.dumps([
            {
                "title": "Draft outline",
                "detail": "Write section headings and bullet points",
                "metric": "5 sections outlined",
                "duration_min": 30,
                "why": "clarity before writing"
            },
            {
                "title": "Collect references",
                "detail": "Save 5 sources to Zotero",
                "metric": "5 sources",
                "duration_min": 25,
                "why": "support arguments"
            }
        ])
        return _resp_with_text(content)

    # Monkeypatch the client method used in gpt.py
    monkeypatch.setattr(gpt.client.chat.completions, "create", fake_create)

    steps = gpt.generate_plan("Write a research paper", None)
    assert isinstance(steps, list) and len(steps) == 2
    assert steps[0]["title"] == "Draft outline"
    # Ensure normalization happened
    assert "detail" in steps[0] and "metric" in steps[0] and "why" in steps[0]
    # Should leave due_date None for UI to set
    assert steps[0]["due_date"] is None
    # Should include order_index and done
    assert "order_index" in steps[0] and steps[0]["done"] == 0

def test_weekly_summary_mock(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    gpt = importlib.import_module("gpt")

    def fake_create(model, messages, temperature):
        return _resp_with_text("Good week. Completed 3/6. Next: draft intro, revise outline, cite sources.")

    monkeypatch.setattr(gpt.client.chat.completions, "create", fake_create)

    steps = [
        {"title": "Draft outline", "metric": "5 sections", "done": 1, "due_date": None},
        {"title": "Collect references", "metric": "5 sources", "done": 0, "due_date": None},
    ]
    checks = [{"day": "2025-10-25"}, {"day": "2025-10-26"}]
    summary = gpt.weekly_summary(steps, checks)
    assert "Good week" in summary and "Next:" in summary

def test_short_quote_mock(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    gpt = importlib.import_module("gpt")

    def fake_create(model, messages, temperature):
        return _resp_with_text("Keep going.")

    monkeypatch.setattr(gpt.client.chat.completions, "create", fake_create)

    q = gpt.short_quote()
    assert isinstance(q, str) and len(q) <= 50 and "Keep" in q
