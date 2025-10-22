import pytest
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_add_event_wrong_format(monkeypatch):
    from src import bot as botmod

    # подменим scheduler.add_job, чтобы не дергать реальный APScheduler
    monkeypatch.setattr(botmod.scheduler, "add_job", lambda *a, **k: None)

    answered = {}
    class FakeMsg:
        text = "/addevent 2025/10/10 10-00 Meeting"  # неправильный формат
        from_user = SimpleNamespace(id=42)
        async def answer(self, text): answered["text"] = text

    await botmod.add_event(FakeMsg())
    assert "Wrong date format" in answered["text"]

@pytest.mark.asyncio
async def test_add_event_too_few_args():
    from src import bot as botmod

    answered = {}
    class FakeMsg:
        text = "/addevent 2025-10-10"  # мало аргументов
        from_user = SimpleNamespace(id=42)
        async def answer(self, text): answered["text"] = text

    await botmod.add_event(FakeMsg())
    assert "Format: /addevent" in answered["text"]
