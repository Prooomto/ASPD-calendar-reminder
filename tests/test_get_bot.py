import pytest

def test_get_bot_no_token(monkeypatch):
    from src import bot as botmod
    # wipe env and constant
    monkeypatch.setenv("BOT_TOKEN", "", prepend=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "", prepend=False)
    monkeypatch.setattr(botmod, "TOKEN", "", raising=False)
    # ensure cache clear
    monkeypatch.setattr(botmod, "_bot", None, raising=False)

    with pytest.raises(RuntimeError):
        botmod.get_bot()

@pytest.mark.asyncio
async def test_get_bot_singleton_and_send(monkeypatch):
    from src import bot as botmod

    class FakeBot:
        def __init__(self, token): self.token = token
        async def send_message(self, chat_id, text): 
            # Simulate send
            assert str(chat_id).isdigit()
            assert text.startswith("🔔 Reminder:")

    monkeypatch.setenv("BOT_TOKEN", "123:abc", prepend=False)
    monkeypatch.setattr(botmod, "_bot", None, raising=False)
    monkeypatch.setattr(botmod, "Bot", FakeBot, raising=True)

    b1 = botmod.get_bot()
    b2 = botmod.get_bot()
    assert b1 is b2

    await botmod.send_reminder(123, "test message")
