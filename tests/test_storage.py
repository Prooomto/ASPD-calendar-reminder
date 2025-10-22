import json
from pathlib import Path

def test_storage_save_and_load(monkeypatch, tmp_path):
    from src import bot as botmod
    tmp_json = tmp_path / "storage.json"
    monkeypatch.setattr(botmod, "DATA_FILE", str(tmp_json), raising=False)

    sample = {"123": [{"time": "2025-01-01T10:00:00", "text": "Hello"}]}
    botmod.save_events(sample)

    assert tmp_json.exists()
    on_disk = json.loads(tmp_json.read_text(encoding="utf-8"))
    assert on_disk == sample

    loaded = botmod.load_events()
    assert loaded == sample

def test_list_events_text(monkeypatch, tmp_path):
    from src import bot as botmod
    tmp_json = tmp_path / "storage.json"
    monkeypatch.setattr(botmod, "DATA_FILE", str(tmp_json), raising=False)

    # empty -> no events
    assert botmod.list_events_text(42) == "You have no events."

    # add and list
    botmod.save_events({"42":[{"time": "2025-01-01T10:00:00", "text": "Hello"}]})
    txt = botmod.list_events_text(42)
    assert "Hello" in txt and "2025-01-01T10:00:00" in txt
