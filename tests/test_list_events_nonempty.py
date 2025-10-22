import pytest
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_list_events_nonempty(monkeypatch):
    from src import bot as botmod

    sample = {"123": [{"time": "2025-01-01T10:00:00", "text": "Hello"}]}
    monkeypatch.setattr(botmod, "load_events", lambda: sample)

    replied = {}
    class FakeMsg:
        from_user = SimpleNamespace(id=123)
        async def answer(self, text): replied["text"] = text

    await botmod.list_events(FakeMsg())
    assert "Your events" in replied["text"]
    assert "2025-01-01T10:00:00" in replied["text"]
    assert "Hello" in replied["text"]
