import pytest

@pytest.mark.asyncio
async def test_send_reminder_uses_bot(monkeypatch):
    from src import bot as botmod

    class FakeBot:
        def __init__(self): self.sent=[]
        async def send_message(self, chat_id, text): self.sent.append((chat_id, text))

    fake = FakeBot()
    monkeypatch.setattr(botmod, "get_bot", lambda: fake)

    await botmod.send_reminder("777", "Ping")
    assert len(fake.sent) == 1
    chat_id, msg = fake.sent[0]
    assert chat_id == "777"
    assert "Ping" in msg  