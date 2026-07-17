import pytest
from types import SimpleNamespace


@pytest.fixture
def client(monkeypatch):
    import app as app_module

    # Stub out heavy dependencies
    app_module.model = SimpleNamespace(predict=lambda df: [7.5])

    # Use a small deterministic dataframe-like object
    class DummyDF:
        def __init__(self):
            self.columns = ["Source Title"]
            self._rows = [
                {"Source Title": "Venue A"},
                {"Source Title": "Venue B"},
                {"Source Title": "Venue C"},
            ]

        @property
        def empty(self):
            return False

        def __len__(self):
            return len(self._rows)

        def __getitem__(self, key):
            if key == "Source Title":
                return self
            raise KeyError(key)

        def fillna(self, _):
            return self

        def tolist(self):
            return [r["Source Title"] for r in self._rows]

        @property
        def iloc(self):
            class _ILoc:
                def __init__(self, rows):
                    self._rows = rows

                def __getitem__(self, idx):
                    return self._rows[idx]

            return _ILoc(self._rows)

    app_module.dataset = DummyDF()

    # Ensure venue recommender dependency exists
    app_module.venue_db = SimpleNamespace(empty=False)

    # Mock PDF extraction
    monkeypatch.setattr(
        app_module,
        "extract_text_from_pdf",
        lambda _file_bytes: "This is an abstract. Abstract\nWe propose a method. Introduction starts here. conclusion exists.",
    )

    # Mock async queue + redis usage for predict tests
    monkeypatch.setattr(app_module, "cache_get_json", lambda _k: None)
    monkeypatch.setattr(app_module, "cache_set_json", lambda *_args, **_kwargs: None)

    app = app_module.app
    app.testing = True
    return app.test_client()

