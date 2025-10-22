import importlib
import os

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
