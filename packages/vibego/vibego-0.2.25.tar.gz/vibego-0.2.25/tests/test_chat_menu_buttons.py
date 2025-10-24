import os
os.environ.setdefault("BOT_TOKEN", "dummy-token")

import asyncio
import json
from unittest.mock import AsyncMock
from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import MenuButtonCommands, ReplyKeyboardMarkup, KeyboardButton

import bot
import master


def test_worker_menu_button_sets_commands_text():
    mock_bot = AsyncMock()
    asyncio.run(bot._ensure_worker_menu_button(mock_bot))
    mock_bot.set_chat_menu_button.assert_awaited_once()
    menu_button = mock_bot.set_chat_menu_button.await_args.kwargs["menu_button"]
    assert isinstance(menu_button, MenuButtonCommands)
    assert menu_button.text == bot.WORKER_MENU_BUTTON_TEXT


def test_worker_menu_button_handles_bad_request(caplog):
    mock_bot = AsyncMock()
    mock_bot.set_chat_menu_button.side_effect = TelegramBadRequest(method=None, message="bad request")
    with caplog.at_level("WARNING"):
        asyncio.run(bot._ensure_worker_menu_button(mock_bot))
    assert mock_bot.set_chat_menu_button.await_count == 1


def test_worker_keyboard_structure():
    markup = bot._build_worker_main_keyboard()
    assert isinstance(markup, ReplyKeyboardMarkup)
    assert len(markup.keyboard) == 1
    assert len(markup.keyboard[0]) == 2
    for button in markup.keyboard[0]:
        assert isinstance(button, KeyboardButton)


def test_worker_keyboard_button_text():
    markup = bot._build_worker_main_keyboard()
    assert markup.keyboard[0][0].text == bot.WORKER_MENU_BUTTON_TEXT
    assert markup.keyboard[0][1].text == bot.WORKER_CREATE_TASK_BUTTON_TEXT


def test_worker_keyboard_resize_enabled():
    markup = bot._build_worker_main_keyboard()
    assert markup.resize_keyboard is True


def test_master_menu_button_sets_commands_text():
    mock_bot = AsyncMock()
    asyncio.run(master._ensure_master_menu_button(mock_bot))
    mock_bot.set_chat_menu_button.assert_awaited_once()
    menu_button = mock_bot.set_chat_menu_button.await_args.kwargs["menu_button"]
    assert isinstance(menu_button, MenuButtonCommands)
    assert menu_button.text == master.MASTER_MENU_BUTTON_TEXT


def test_master_menu_button_handles_bad_request(caplog):
    mock_bot = AsyncMock()
    mock_bot.set_chat_menu_button.side_effect = TelegramBadRequest(method=None, message="bad request")
    with caplog.at_level("WARNING"):
        asyncio.run(master._ensure_master_menu_button(mock_bot))
    assert mock_bot.set_chat_menu_button.await_count == 1


def test_master_keyboard_structure():
    markup = master._build_master_main_keyboard()
    assert isinstance(markup, ReplyKeyboardMarkup)
    assert len(markup.keyboard) == 1
    assert len(markup.keyboard[0]) == 2
    assert isinstance(markup.keyboard[0][0], KeyboardButton)
    assert isinstance(markup.keyboard[0][1], KeyboardButton)


def test_master_keyboard_button_text():
    markup = master._build_master_main_keyboard()
    assert markup.keyboard[0][0].text == master.MASTER_MENU_BUTTON_TEXT
    assert markup.keyboard[0][1].text == master.MASTER_MANAGE_BUTTON_TEXT


def test_master_keyboard_resize_enabled():
    markup = master._build_master_main_keyboard()
    assert markup.resize_keyboard is True


def test_master_commands_sync_calls_set_my_commands():
    mock_bot = AsyncMock()
    asyncio.run(master._ensure_master_commands(mock_bot))
    assert mock_bot.set_my_commands.await_count == 4


def test_master_commands_handles_bad_request(caplog):
    mock_bot = AsyncMock()
    mock_bot.set_my_commands.side_effect = master.TelegramBadRequest(method=None, message="bad request")
    with caplog.at_level("WARNING"):
        asyncio.run(master._ensure_master_commands(mock_bot))
    assert mock_bot.set_my_commands.await_count == 4


def test_master_broadcast_sends_to_admins_and_state(caplog):
    class DummyStateStore:
        def __init__(self):
            self.data = {"default": master.ProjectState(model="codex", status="running", chat_id=456)}

        def refresh(self):
            return

    class DummyManager:
        def __init__(self):
            self.admin_ids = {123}
            self.state_store = DummyStateStore()
            self._refreshed = False

        def refresh_state(self):
            self._refreshed = True

    manager = DummyManager()
    mock_bot = AsyncMock()

    with caplog.at_level("INFO"):
        asyncio.run(master._broadcast_master_keyboard(mock_bot, manager))
    assert manager._refreshed is True
    assert mock_bot.send_message.await_count == 0


def test_master_broadcast_handles_empty_targets(caplog):
    class DummyStateStore:
        def __init__(self):
            self.data = {}

        def refresh(self):
            return

    class DummyManager:
        def __init__(self):
            self.admin_ids = set()
            self.state_store = DummyStateStore()
            self._refreshed = False

        def refresh_state(self):
            self._refreshed = True

    manager = DummyManager()
    mock_bot = AsyncMock()
    with caplog.at_level("INFO"):
        asyncio.run(master._broadcast_master_keyboard(mock_bot, manager))
    assert manager._refreshed is True
    assert mock_bot.send_message.await_count == 0


class _DummyMessage:
    """用于模拟 master 项目按钮触发的测试消息。"""

    def __init__(self, text: str, chat_id: int = 999, message_id: int = 123) -> None:
        self.text = text
        self.message_id = message_id
        self.chat = SimpleNamespace(id=chat_id)
        self.from_user = SimpleNamespace(id=chat_id, username=None)
        self.bot = AsyncMock()
        self._answers = []

    async def answer(self, text: str, **kwargs):
        self._answers.append((text, kwargs))


class _DummyManager:
    """模拟授权通过的 master manager。"""

    def __init__(self) -> None:
        self.invocations = []

    def is_authorized(self, chat_id: int) -> bool:
        self.invocations.append(chat_id)
        return True


def test_master_projects_button_accepts_legacy_text(monkeypatch):
    dummy_manager = _DummyManager()

    async def fake_ensure_manager():
        return dummy_manager

    send_calls = []

    async def fake_send(bot, chat_id, manager, reply_to_message_id=None):
        send_calls.append((chat_id, reply_to_message_id))

    monkeypatch.setattr(master, "_ensure_manager", fake_ensure_manager)
    monkeypatch.setattr(master, "_send_projects_overview_to_chat", fake_send)

    message = _DummyMessage("📂 Projects")
    asyncio.run(master.on_master_projects_button(message))

    assert len(message._answers) == 1
    _, kwargs = message._answers[0]
    assert isinstance(kwargs["reply_markup"], ReplyKeyboardMarkup)
    assert kwargs["reply_markup"].keyboard[0][0].text == master.MASTER_MENU_BUTTON_TEXT
    assert kwargs["reply_markup"].keyboard[0][1].text == master.MASTER_MANAGE_BUTTON_TEXT
    assert send_calls == [(message.chat.id, None)]


def test_master_projects_button_uses_new_text_without_refresh(monkeypatch):
    dummy_manager = _DummyManager()

    async def fake_ensure_manager():
        return dummy_manager

    send_calls = []

    async def fake_send(bot, chat_id, manager, reply_to_message_id=None):
        send_calls.append((chat_id, reply_to_message_id))

    monkeypatch.setattr(master, "_ensure_manager", fake_ensure_manager)
    monkeypatch.setattr(master, "_send_projects_overview_to_chat", fake_send)

    message = _DummyMessage(master.MASTER_MENU_BUTTON_TEXT)
    asyncio.run(master.on_master_projects_button(message))

    assert message._answers == []
    assert send_calls == [(message.chat.id, message.message_id)]


def test_worker_resolve_targets_reads_state_and_config(tmp_path, monkeypatch):
    slug = bot.PROJECT_SLUG
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({slug: {"chat_id": 111}}), encoding="utf-8")
    projects_file = tmp_path / "projects.json"
    projects_file.write_text(
        json.dumps([{"project_slug": slug, "bot_name": bot.PROJECT_NAME or slug, "allowed_chat_id": "222"}]),
        encoding="utf-8",
    )
    monkeypatch.setenv("STATE_FILE", str(state_file))
    monkeypatch.setenv("MASTER_PROJECTS_PATH", str(projects_file))
    monkeypatch.delenv("ALLOWED_CHAT_ID", raising=False)
    monkeypatch.delenv("WORKER_CHAT_ID", raising=False)

    targets = bot._resolve_worker_target_chat_ids()
    assert targets == [111, 222]

    monkeypatch.delenv("STATE_FILE", raising=False)
    monkeypatch.delenv("MASTER_PROJECTS_PATH", raising=False)


def test_worker_broadcast_pushes_to_targets(tmp_path, monkeypatch):
    slug = bot.PROJECT_SLUG
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({slug: {"chat_id": 333}}), encoding="utf-8")
    projects_file = tmp_path / "projects.json"
    projects_file.write_text(
        json.dumps([{"project_slug": slug, "bot_name": bot.PROJECT_NAME or slug, "allowed_chat_id": "444"}]),
        encoding="utf-8",
    )
    monkeypatch.setenv("STATE_FILE", str(state_file))
    monkeypatch.setenv("MASTER_PROJECTS_PATH", str(projects_file))
    monkeypatch.delenv("ALLOWED_CHAT_ID", raising=False)
    monkeypatch.delenv("WORKER_CHAT_ID", raising=False)

    mock_bot = AsyncMock()
    asyncio.run(bot._broadcast_worker_keyboard(mock_bot))
    assert mock_bot.send_message.await_count == 2
    payload = {call.kwargs["chat_id"] for call in mock_bot.send_message.await_args_list}
    assert payload == {333, 444}

    monkeypatch.delenv("STATE_FILE", raising=False)
    monkeypatch.delenv("MASTER_PROJECTS_PATH", raising=False)
