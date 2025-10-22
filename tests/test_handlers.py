# tests/test_handlers.py
import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_start_command(monkeypatch):
    from src import bot as botmod

    # фейковое сообщение с корутиной answer
    answered = {}
    class FakeMsg:
        async def answer(self, text):
            answered["text"] = text
    msg = FakeMsg()

    await botmod.start_command(msg)
    assert "Use /addevent" in answered["text"]

@pytest.mark.asyncio
async def test_add_event_success(monkeypatch, tmp_path):
    from src import bot as botmod

    # подменим storage.json в tmp
    monkeypatch.setattr(botmod, "DATA_FILE", str(tmp_path / "storage.json"), raising=False)

    # собираем валидное время через +2 минуты
    t = (datetime.utcnow() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
    answered = {}

    class FakeUser: id = 123
    class FakeMsg:
        text = f"/addevent {t} Standup"
        from_user = SimpleNamespace(id=FakeUser.id)
        async def answer(self, text): answered["text"] = text

    # заглушим планировщик, чтобы не стартовал реальную job
    monkeypatch.setattr(botmod.scheduler, "add_job", lambda *a, **k: None)

    await botmod.add_event(FakeMsg())
    assert "Event added for" in answered["text"]

@pytest.mark.asyncio
async def test_list_events_empty(monkeypatch):
    from src import bot as botmod
    monkeypatch.setattr(botmod, "load_events", lambda: {})
    answered = {}
    class FakeMsg:
        from_user = SimpleNamespace(id=999)
        async def answer(self, text): answered["text"] = text
    await botmod.list_events(FakeMsg())
    assert "No events" in answered["text"]
