import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_add_event_schedules_job(monkeypatch, tmp_path):
    from src import bot as botmod

    # Используем временный файл для хранилища
    monkeypatch.setattr(botmod, "DATA_FILE", str(tmp_path / "storage.json"), raising=False)

    captured = {}
    def fake_add_job(func, trigger, run_date, args):
        captured["trigger"] = trigger
        captured["run_date"] = run_date
        captured["args"] = args
        return SimpleNamespace(id="job-1")

    monkeypatch.setattr(botmod.scheduler, "add_job", fake_add_job)

    # Время +2 минуты, чтобы прошло валидацию
    t = (datetime.utcnow() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")

    replied = {}
    class FakeMsg:
        text = f"/addevent {t} Important"
        from_user = SimpleNamespace(id=777)
        async def answer(self, text): replied["text"] = text

    await botmod.add_event(FakeMsg())

    assert captured["trigger"] == "date"
    assert isinstance(captured["run_date"], datetime)
    assert captured["args"] == ["777", "Important"]
    assert "Event added for" in replied["text"]
