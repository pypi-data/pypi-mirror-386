import importlib
import os
import time
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("MODE", "B")
os.environ.setdefault("ACTIVE_MODEL", "claudecode")

bot = importlib.import_module("bot")


def test_extract_claudecode_assistant_message():
    event = {
        "type": "assistant",
        "message": {
            "id": "msg_test",
            "content": [
                {"type": "thinking", "thinking": "隐藏思考"},
                {"type": "text", "text": "第一段输出"},
                {"type": "tool_use", "name": "Bash", "input": {"command": "pwd"}},
                {"type": "text", "text": "第二段输出"},
            ],
        },
    }
    result = bot._extract_deliverable_payload(event, event_timestamp=None)
    assert result is not None
    kind, text, metadata = result
    assert kind == bot.DELIVERABLE_KIND_MESSAGE
    assert "第一段输出" in text and "第二段输出" in text
    assert metadata == {"message_id": "msg_test"}


def test_extract_claudecode_assistant_tool_result():
    event = {
        "type": "assistant",
        "message": {
            "id": "msg_tool",
            "content": [
                {
                    "type": "tool_result",
                    "output": "/Users/david/project",
                    "content": "/Users/david/project",
                    "is_error": False,
                }
            ],
        },
    }
    result = bot._extract_deliverable_payload(event, event_timestamp=None)
    assert result is not None
    kind, text, metadata = result
    assert kind == bot.DELIVERABLE_KIND_MESSAGE
    assert "/Users/david/project" in text
    assert metadata == {"message_id": "msg_tool"}


def test_claudecode_fallback_selects_latest(tmp_path):
    pointer = tmp_path / "current_session.txt"
    old_file = tmp_path / "rollout-old.jsonl"
    new_dir = tmp_path / "sessions"
    new_dir.mkdir()
    new_file = new_dir / "rollout-20250101.jsonl"

    old_file.write_text("{}", encoding="utf-8")
    pointer.write_text(str(old_file), encoding="utf-8")
    new_file.write_text("{}", encoding="utf-8")
    os.utime(old_file, (time.time() - 60, time.time() - 60))
    os.utime(new_file, (time.time(), time.time()))

    previous_root = bot.MODEL_SESSION_ROOT
    try:
        bot.MODEL_SESSION_ROOT = str(tmp_path)
        result = bot._find_latest_claudecode_rollout(pointer)
    finally:
        bot.MODEL_SESSION_ROOT = previous_root

    assert result == new_file
