import io
import json
from types import SimpleNamespace

import pytest


def test_recommend_propagates_backend_error(monkeypatch, client):
    import app as app_module

    def fake_recommend_venues_enhanced(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "recommend_venues_enhanced", fake_recommend_venues_enhanced)

    resp = client.post(
        "/recommend",
        data=json.dumps(
            {
                "paper_text": "This is a sufficiently long paper text. " * 20,
                "paper_score": 7.0,
                "paper_topic": "",
                "venue_type": "journal",
                "indexing": ["Any"],
                "fee_pref": "Any",
                "acceptance": "Any",
            }
        ),
        content_type="application/json",
    )

    # Depending on backend exception handling, could be 500 with error key
    payload = resp.get_json(silent=True) or {}
    assert resp.status_code in (500, 503)
    assert "error" in payload

