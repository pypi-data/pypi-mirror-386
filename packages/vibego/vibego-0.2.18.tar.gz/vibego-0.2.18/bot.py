# bot.py — Telegram 提示词 → Mac 执行 → 回推 (aiogram 3.x)
# 说明：
# - 使用长轮询，不需要公网端口；
# - MODE=A: 直接以子进程方式调用你的 agent/codex CLI/HTTP（此处给出 CLI 示例）；
# - MODE=B: 将提示词注入 tmux 会话（如 vibe），依靠 pipe-pane 写入的日志抽取本次输出；
# - 安全：仅允许 ALLOWED_CHAT_ID（私聊你的 chat_id）；BOT_TOKEN 从 .env 读取；不要把 token 写进代码。

from __future__ import annotations

import asyncio, os, sys, time, uuid, shlex, subprocess, socket, re, json, shutil, hashlib, html
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, List, Callable, Awaitable, Literal
from dataclasses import dataclass
from urllib.parse import urlparse, quote, unquote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    BufferedInputFile,
    CallbackQuery,
    MessageEntity,
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonCommands,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User,
)
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.utils.formatting import Text
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramForbiddenError,
)
from aiohttp import BasicAuth, ClientError

from logging_setup import create_logger
from tasks import TaskHistoryRecord, TaskNoteRecord, TaskRecord, TaskService
from tasks.commands import parse_simple_kv, parse_structured_text
from tasks.constants import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_PRIORITY,
    NOTE_TYPES,
    STATUS_ALIASES,
    TASK_STATUSES,
    TASK_TYPES,
)
from tasks.fsm import (
    TaskBugReportStates,
    TaskCreateStates,
    TaskDescriptionStates,
    TaskEditStates,
    TaskListSearchStates,
    TaskNoteStates,
    TaskPushStates,
)

# --- 简单 .env 加载 ---
def load_env(p: str = ".env"):
    """从指定路径加载 dotenv 格式的键值对到进程环境变量。"""

    if not os.path.exists(p): 
        return
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"): 
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env()

# --- 日志 & 上下文 ---
PROJECT_NAME = os.environ.get("PROJECT_NAME", "").strip()
ACTIVE_MODEL = (os.environ.get("ACTIVE_MODEL") or os.environ.get("MODEL_NAME") or "").strip()
worker_log = create_logger(
    "worker",
    project=PROJECT_NAME or "-",
    model=ACTIVE_MODEL or "-",
    level_env="WORKER_LOG_LEVEL",
    stderr_env="WORKER_STDERR",
)

def _env_int(name: str, default: int) -> int:
    """读取整型环境变量，解析失败时回退默认值。"""

    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        worker_log.warning("环境变量 %s=%r 解析为整数失败，已使用默认值 %s", name, raw, default)
        return default

_PARSE_MODE_CANDIDATES: Dict[str, Optional[ParseMode]] = {
    "": None,
    "none": None,
    "markdown": ParseMode.MARKDOWN,
    "md": ParseMode.MARKDOWN,
    "markdownv2": ParseMode.MARKDOWN_V2,
    "mdv2": ParseMode.MARKDOWN_V2,
    "html": ParseMode.HTML,
}

# 阶段提示统一追加 agents.md 信息，确保推送记录要求一致。
AGENTS_PHASE_SUFFIX = "，最后列出当前所触发的 agents.md 的阶段、任务名称、任务编码（例：/TASK_0001）。"
# 推送到模型的阶段提示（vibe 与测试），合并统一后缀确保输出一致。
VIBE_PHASE_PROMPT = f"进入vibe阶段{AGENTS_PHASE_SUFFIX}"
TEST_PHASE_PROMPT = f"进入测试阶段{AGENTS_PHASE_SUFFIX}"

_parse_mode_env = (os.environ.get("TELEGRAM_PARSE_MODE") or "MarkdownV2").strip()
_parse_mode_key = _parse_mode_env.replace("-", "").replace("_", "").lower()
MODEL_OUTPUT_PARSE_MODE: Optional[ParseMode]
if _parse_mode_key in _PARSE_MODE_CANDIDATES:
    MODEL_OUTPUT_PARSE_MODE = _PARSE_MODE_CANDIDATES[_parse_mode_key]
    if MODEL_OUTPUT_PARSE_MODE is None:
        worker_log.info("模型输出将按纯文本发送")
    else:
        worker_log.info("模型输出 parse_mode：%s", MODEL_OUTPUT_PARSE_MODE.value)
else:
    MODEL_OUTPUT_PARSE_MODE = ParseMode.MARKDOWN_V2
    worker_log.warning(
        "未识别的 TELEGRAM_PARSE_MODE=%s，回退为 MarkdownV2",
        _parse_mode_env,
    )

_plan_parse_mode_env = (os.environ.get("PLAN_PROGRESS_PARSE_MODE") or "").strip()
_plan_parse_mode_key = _plan_parse_mode_env.replace("-", "").replace("_", "").lower()
PLAN_PROGRESS_PARSE_MODE: Optional[ParseMode]
if not _plan_parse_mode_key:
    PLAN_PROGRESS_PARSE_MODE = None
    worker_log.info("计划进度消息默认按纯文本发送")
elif _plan_parse_mode_key in _PARSE_MODE_CANDIDATES:
    PLAN_PROGRESS_PARSE_MODE = _PARSE_MODE_CANDIDATES[_plan_parse_mode_key]
    if PLAN_PROGRESS_PARSE_MODE is None:
        worker_log.info("计划进度消息将按纯文本发送")
    else:
        mode_value = (
            PLAN_PROGRESS_PARSE_MODE.value
            if isinstance(PLAN_PROGRESS_PARSE_MODE, ParseMode)
            else str(PLAN_PROGRESS_PARSE_MODE)
        )
        worker_log.info("计划进度消息 parse_mode：%s", mode_value)
else:
    PLAN_PROGRESS_PARSE_MODE = None
    worker_log.warning(
        "未识别的 PLAN_PROGRESS_PARSE_MODE=%s，计划进度消息将按纯文本发送",
        _plan_parse_mode_env,
    )

_IS_MARKDOWN_V2 = MODEL_OUTPUT_PARSE_MODE == ParseMode.MARKDOWN_V2
_IS_MARKDOWN = MODEL_OUTPUT_PARSE_MODE == ParseMode.MARKDOWN


def _parse_mode_value() -> Optional[str]:
    """返回模型输出使用的 Telegram parse_mode 值。"""

    if MODEL_OUTPUT_PARSE_MODE is None:
        return None
    return MODEL_OUTPUT_PARSE_MODE.value if isinstance(MODEL_OUTPUT_PARSE_MODE, ParseMode) else str(MODEL_OUTPUT_PARSE_MODE)


def _plan_parse_mode_value() -> Optional[str]:
    """返回计划进度消息使用的 Telegram parse_mode 值。"""

    if PLAN_PROGRESS_PARSE_MODE is None:
        return None
    return (
        PLAN_PROGRESS_PARSE_MODE.value
        if isinstance(PLAN_PROGRESS_PARSE_MODE, ParseMode)
        else str(PLAN_PROGRESS_PARSE_MODE)
    )

# --- 配置 ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
if not BOT_TOKEN:
    worker_log.error("BOT_TOKEN 未配置，程序退出")
    sys.exit(1)

MODE = os.environ.get("MODE", "B").upper()                      # A 或 B

# 模式A（CLI）
AGENT_CMD = os.environ.get("AGENT_CMD", "")  # 例如: codex --project /path/to/proj --prompt -
# 可扩展 HTTP：AGENT_HTTP=http://127.0.0.1:7001/api/run

# 模式B（tmux）
TMUX_SESSION = os.environ.get("TMUX_SESSION", "vibe")
TMUX_LOG = os.environ.get("TMUX_LOG", str(Path(__file__).resolve().parent / "vibe.out.log"))
IDLE_SECONDS = float(os.environ.get("IDLE_SECONDS", "3"))
MAX_RETURN_CHARS = int(os.environ.get("MAX_RETURN_CHARS", "200000"))  # 超大文本转附件
TELEGRAM_PROXY = os.environ.get("TELEGRAM_PROXY", "").strip()        # 可选代理 URL
CODEX_WORKDIR = os.environ.get("CODEX_WORKDIR", "").strip()
CODEX_SESSION_FILE_PATH = os.environ.get("CODEX_SESSION_FILE_PATH", "").strip()
CODEX_SESSIONS_ROOT = os.environ.get("CODEX_SESSIONS_ROOT", "").strip()
MODEL_SESSION_ROOT = os.environ.get("MODEL_SESSION_ROOT", "").strip()
MODEL_SESSION_GLOB = os.environ.get("MODEL_SESSION_GLOB", "rollout-*.jsonl").strip() or "rollout-*.jsonl"
SESSION_POLL_TIMEOUT = float(os.environ.get("SESSION_POLL_TIMEOUT", "2"))
WATCH_MAX_WAIT = float(os.environ.get("WATCH_MAX_WAIT", "0"))
WATCH_INTERVAL = float(os.environ.get("WATCH_INTERVAL", "2"))
SEND_RETRY_ATTEMPTS = int(os.environ.get("SEND_RETRY_ATTEMPTS", "3"))
SEND_RETRY_BASE_DELAY = float(os.environ.get("SEND_RETRY_BASE_DELAY", "0.5"))
SEND_FAILURE_NOTICE_COOLDOWN = float(os.environ.get("SEND_FAILURE_NOTICE_COOLDOWN", "30"))
SESSION_INITIAL_BACKTRACK_BYTES = int(os.environ.get("SESSION_INITIAL_BACKTRACK_BYTES", "16384"))
ENABLE_PLAN_PROGRESS = (os.environ.get("ENABLE_PLAN_PROGRESS", "1").strip().lower() not in {"0", "false", "no", "off"})
AUTO_COMPACT_THRESHOLD = max(_env_int("AUTO_COMPACT_THRESHOLD", 0), 0)

PLAN_STATUS_LABELS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
}

DELIVERABLE_KIND_MESSAGE = "message"
DELIVERABLE_KIND_PLAN = "plan_update"
MODEL_COMPLETION_PREFIX = "✅模型执行完成，响应结果如下："
TELEGRAM_MESSAGE_LIMIT = 4096  # Telegram sendMessage 单条上限


def _canonical_model_name(raw_model: Optional[str] = None) -> str:
    """标准化模型名称，便于后续按模型分支处理。"""

    source = raw_model
    if source is None:
        source = (os.environ.get("MODEL_NAME") or ACTIVE_MODEL or "codex").strip()
    normalized = source.replace("-", "").replace("_", "").lower()
    return normalized or "codex"


def _model_display_label() -> str:
    """返回当前活跃模型的友好名称。"""

    raw = (os.environ.get("MODEL_NAME") or ACTIVE_MODEL or "codex").strip()
    normalized = _canonical_model_name(raw)
    mapping = {
        "codex": "Codex",
        "claudecode": "ClaudeCode",
        "gemini": "Gemini",
    }
    return mapping.get(normalized, raw or "模型")


MODEL_CANONICAL_NAME = _canonical_model_name()
MODEL_DISPLAY_LABEL = _model_display_label()


def _is_claudecode_model() -> bool:
    """判断当前 worker 是否运行 ClaudeCode 模型。"""

    return MODEL_CANONICAL_NAME == "claudecode"


@dataclass
class SessionDeliverable:
    """描述 JSONL 会话中的单个推送事件。"""

    offset: int
    kind: str
    text: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

ENV_ISSUES: list[str] = []
PRIMARY_WORKDIR: Optional[Path] = None

storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
dp.include_router(router)

_bot: Bot | None = None


def _mask_proxy(url: str) -> str:
    """在 stderr 打印代理信息时隐藏凭据"""
    if "@" not in url:
        return url
    parsed = urlparse(url)
    host = parsed.hostname or "***"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://***:***@{host}{port}"


def _detect_proxy() -> tuple[Optional[str], Optional[BasicAuth], Optional[str]]:
    """优先使用 TELEGRAM_PROXY，否则回落到常见环境变量"""
    candidates = [
        ("TELEGRAM_PROXY", TELEGRAM_PROXY),
        ("https_proxy", os.environ.get("https_proxy")),
        ("HTTPS_PROXY", os.environ.get("HTTPS_PROXY")),
        ("http_proxy", os.environ.get("http_proxy")),
        ("HTTP_PROXY", os.environ.get("HTTP_PROXY")),
        ("all_proxy", os.environ.get("all_proxy")),
        ("ALL_PROXY", os.environ.get("ALL_PROXY")),
    ]

    proxy_raw: Optional[str] = None
    source: Optional[str] = None
    for key, value in candidates:
        if value:
            proxy_raw = value.strip()
            source = key
            break

    if not proxy_raw:
        return None, None, None

    parsed = urlparse(proxy_raw)
    auth: Optional[BasicAuth] = None
    if parsed.username:
        password = parsed.password or ""
        auth = BasicAuth(parsed.username, password)
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        proxy_raw = parsed._replace(netloc=netloc, path="", params="", query="", fragment="").geturl()

    worker_log.info("使用代理(%s): %s", source, _mask_proxy(proxy_raw))
    return proxy_raw, auth, source

# 统一以 IPv4 访问 Telegram，避免部分网络环境下 IPv6 连接被丢弃
def build_bot() -> Bot:
    """按照网络环境与代理配置创建 aiogram Bot。"""

    proxy_url, proxy_auth, _ = _detect_proxy()
    session_kwargs = {
        "proxy": proxy_url,
        "timeout": 60,
        "limit": 100,
    }
    if proxy_auth is not None:
        session_kwargs["proxy_auth"] = proxy_auth

    session = AiohttpSession(**session_kwargs)
    # 内部 `_connector_init` 控制 TCPConnector 创建参数，此处强制 IPv4
    session._connector_init.update({  # type: ignore[attr-defined]
        "family": socket.AF_INET,
        "ttl_dns_cache": 60,
    })
    return Bot(token=BOT_TOKEN, session=session)

def current_bot() -> Bot:
    """返回懒加载的全局 Bot 实例。"""

    global _bot
    if _bot is None:
        _bot = build_bot()
    return _bot

# --- 工具函数 ---
async def _send_with_retry(coro_factory, *, attempts: int = SEND_RETRY_ATTEMPTS) -> None:
    """对 Telegram 调用执行有限次重试。"""

    delay = SEND_RETRY_BASE_DELAY
    last_exc: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            await coro_factory()
            return
        except TelegramRetryAfter as exc:
            last_exc = exc
            if attempt >= attempts - 1:
                break
            await asyncio.sleep(max(float(exc.retry_after), SEND_RETRY_BASE_DELAY))
        except TelegramNetworkError as exc:
            last_exc = exc
            if attempt >= attempts - 1:
                break
            await asyncio.sleep(delay)
            delay *= 2
        except TelegramBadRequest:
            raise

    if last_exc is not None:
        raise last_exc


def _escape_markdown_v2(text: str) -> str:
    """转义 MarkdownV2 特殊字符。

    注意：
    - Text().as_markdown() 会转义所有 MarkdownV2 特殊字符
    - 只移除纯英文单词之间的连字符转义（如 "pre-release"）
    - 保留数字、时间戳等其他情况的连字符转义（如 "2025-10-23"）
    """
    escaped = Text(text).as_markdown()
    # 只移除纯英文字母之间的连字符转义（避免影响数字、时间戳等）
    escaped = re.sub(r"(?<=[a-zA-Z])\\-(?=[a-zA-Z])", "-", escaped)
    # 移除斜杠的转义（Telegram 不需要转义斜杠）
    escaped = escaped.replace("\\/", "/")
    return escaped


LEGACY_DOUBLE_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
LEGACY_DOUBLE_UNDERLINE = re.compile(r"__(.+?)__", re.DOTALL)
CODE_SEGMENT_RE = re.compile(r"(```.*?```|`[^`]*`)", re.DOTALL)


def _normalize_legacy_markdown(text: str) -> str:
    def _replace_double_star(match: re.Match[str]) -> str:
        content = match.group(1)
        return f"*{content}*"

    def _replace_double_underline(match: re.Match[str]) -> str:
        content = match.group(1)
        return f"_{content}_"

    def _normalize_segment(segment: str) -> str:
        converted = LEGACY_DOUBLE_BOLD.sub(_replace_double_star, segment)
        converted = LEGACY_DOUBLE_UNDERLINE.sub(_replace_double_underline, converted)
        return converted

    pieces: list[str] = []
    last_index = 0
    for match in CODE_SEGMENT_RE.finditer(text):
        normal_part = text[last_index:match.start()]
        if normal_part:
            pieces.append(_normalize_segment(normal_part))
        pieces.append(match.group(0))
        last_index = match.end()

    if last_index < len(text):
        pieces.append(_normalize_segment(text[last_index:]))

    return "".join(pieces)


def _prepare_model_payload(text: str) -> str:
    if _IS_MARKDOWN_V2:
        return _escape_markdown_v2(text)
    if _IS_MARKDOWN:
        return _normalize_legacy_markdown(text)
    return text


def _extract_bad_request_message(exc: TelegramBadRequest) -> str:
    message = getattr(exc, "message", None)
    if not message:
        args = getattr(exc, "args", ())
        if args:
            message = str(args[0])
        else:
            message = str(exc)
    return message


def _is_markdown_parse_error(exc: TelegramBadRequest) -> bool:
    reason = _extract_bad_request_message(exc).lower()
    return any(
        hint in reason
        for hint in (
            "can't parse entities",
            "can't parse formatted text",
            "wrong entity data",
            "expected end of entity",
        )
    )


def _escape_markdown_legacy(text: str) -> str:
    escape_chars = "_[]()"

    def _escape_segment(segment: str) -> str:
        result = segment
        for ch in escape_chars:
            result = result.replace(ch, f"\\{ch}")
        return result

    pieces: list[str] = []
    last_index = 0
    for match in CODE_SEGMENT_RE.finditer(text):
        normal_part = text[last_index:match.start()]
        if normal_part:
            pieces.append(_escape_segment(normal_part))
        pieces.append(match.group(0))
        last_index = match.end()

    if last_index < len(text):
        pieces.append(_escape_segment(text[last_index:]))

    return "".join(pieces)


async def _send_with_markdown_guard(
    text: str,
    sender: Callable[[str], Awaitable[None]],
    *,
    raw_sender: Optional[Callable[[str], Awaitable[None]]] = None,
) -> str:
    try:
        await sender(text)
        return text
    except TelegramBadRequest as exc:
        if not _is_markdown_parse_error(exc):
            raise

        sanitized: Optional[str]
        if _IS_MARKDOWN_V2:
            sanitized = _escape_markdown_v2(text)
            if "**" in text:
                sanitized = sanitized.replace(r"\*\*", "**")
            if "__" in text:
                sanitized = sanitized.replace(r"\_\_", "__")
            if "```" in text:
                sanitized = sanitized.replace(r"\`\`\`", "```")
            if "`" in text:
                sanitized = sanitized.replace(r"\`", "`")
        elif _IS_MARKDOWN:
            sanitized = _escape_markdown_legacy(text)
        else:
            sanitized = None

        if sanitized and sanitized != text:
            worker_log.debug(
                "Markdown 解析失败，已对文本转义后重试",
                extra={"length": len(text)},
            )
            try:
                await sender(sanitized)
                return sanitized
            except TelegramBadRequest as exc_sanitized:
                if not _is_markdown_parse_error(exc_sanitized):
                    raise

        if raw_sender is None:
            raise

        worker_log.warning(
            "Markdown 解析仍失败，将以纯文本发送",
            extra={"length": len(text)},
        )
        await raw_sender(text)
        return text


async def _notify_send_failure_message(chat_id: int) -> None:
    """向用户提示消息发送存在网络问题，避免重复刷屏。"""

    now = time.monotonic()
    last_notice = CHAT_FAILURE_NOTICES.get(chat_id)
    if last_notice is not None and (now - last_notice) < SEND_FAILURE_NOTICE_COOLDOWN:
        return

    notice = "发送结果时网络出现异常，系统正在尝试重试，请稍后再试。"
    bot = current_bot()

    try:
        async def _send_notice() -> None:
            async def _do() -> None:
                await bot.send_message(chat_id=chat_id, text=notice, parse_mode=None)

            await _send_with_retry(_do)

        await _send_notice()
    except (TelegramNetworkError, TelegramRetryAfter, TelegramBadRequest):
        CHAT_FAILURE_NOTICES[chat_id] = now
        return

    CHAT_FAILURE_NOTICES[chat_id] = now


def _prepend_completion_header(text: str) -> str:
    """为模型输出添加完成提示，避免重复拼接。"""

    if text.startswith(MODEL_COMPLETION_PREFIX):
        return text
    if text:
        return f"{MODEL_COMPLETION_PREFIX}\n\n{text}"
    return MODEL_COMPLETION_PREFIX

# pylint: disable=too-many-locals
async def reply_large_text(
    chat_id: int,
    text: str,
    *,
    parse_mode: Optional[str] = None,
    preformatted: bool = False,
) -> str:
    """向指定会话发送可能较长的文本，必要时退化为附件。

    :param chat_id: Telegram 会话标识。
    :param text: 待发送内容。
    :param parse_mode: 指定消息的 parse_mode，未提供时沿用全局默认值。
    :param preformatted: 标记文本已按 parse_mode 处理，跳过内部转义。
    """
    bot = current_bot()
    parse_mode_value = parse_mode if parse_mode is not None else _parse_mode_value()
    prepared = text if preformatted else _prepare_model_payload(text)

    async def _send_formatted_message(payload: str) -> None:
        await bot.send_message(
            chat_id=chat_id,
            text=payload,
            parse_mode=parse_mode_value,
        )

    async def _send_raw_message(payload: str) -> None:
        await bot.send_message(chat_id=chat_id, text=payload, parse_mode=None)

    if len(prepared) <= TELEGRAM_MESSAGE_LIMIT:
        delivered = await _send_with_markdown_guard(
            prepared,
            _send_formatted_message,
            raw_sender=_send_raw_message,
        )

        worker_log.info(
            "完成单条消息发送",
            extra={
                "chat": chat_id,
                "mode": "single",
                "length": str(len(delivered)),
            },
        )
        return delivered

    attachment_name = f"model-response-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    summary_text = (
        f"{MODEL_COMPLETION_PREFIX}\n\n"
        f"内容较长，已生成附件 `{attachment_name}`，请下载查看全文。"
    )

    delivered_summary = await _send_with_markdown_guard(
        summary_text,
        _send_formatted_message,
        raw_sender=_send_raw_message,
    )

    document = BufferedInputFile(text.encode("utf-8"), filename=attachment_name)

    async def _send_document() -> None:
        await bot.send_document(chat_id=chat_id, document=document)

    await _send_with_retry(_send_document)

    worker_log.info(
        "长文本已转附件发送",
        extra={
            "chat": chat_id,
            "mode": "attachment",
            "length": str(len(prepared)),
            "attachment_name": attachment_name,
        },
    )

    return delivered_summary

def run_subprocess_capture(cmd: str, input_text: str = "") -> Tuple[int, str]:
    # 同步执行 CLI，stdin 喂 prompt，捕获 stdout+stderr
    p = subprocess.Popen(
        shlex.split(cmd),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )
    out, _ = p.communicate(input=input_text, timeout=None)
    return p.returncode, out

def tmux_bin() -> str:
    return subprocess.check_output("command -v tmux", shell=True, text=True).strip()


def _tmux_cmd(tmux: str, *args: str) -> list[str]:
    return [tmux, "-u", *args]


def tmux_send_line(session: str, line: str):
    tmux = tmux_bin()
    subprocess.check_call(_tmux_cmd(tmux, "has-session", "-t", session))
    # 发送一次 ESC，退出 Codex 可能的菜单或输入模式
    subprocess.call(
        _tmux_cmd(tmux, "send-keys", "-t", session, "Escape"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.05)
    try:
        pane_in_mode = subprocess.check_output(
            _tmux_cmd(tmux, "display-message", "-p", "-t", session, "#{pane_in_mode}"),
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        pane_in_mode = "0"
    if pane_in_mode == "1":
        subprocess.check_call(_tmux_cmd(tmux, "send-keys", "-t", session, "-X", "cancel"))
        time.sleep(0.05)
    chunks = line.split("\n")
    for idx, chunk in enumerate(chunks):
        if chunk:
            subprocess.check_call(_tmux_cmd(tmux, "send-keys", "-t", session, "--", chunk))
        if idx < len(chunks) - 1:
            subprocess.check_call(_tmux_cmd(tmux, "send-keys", "-t", session, "C-j"))
            time.sleep(0.05)
    time.sleep(0.05)
    subprocess.check_call(_tmux_cmd(tmux, "send-keys", "-t", session, "C-m"))


def resolve_path(path: Path | str) -> Path:
    if isinstance(path, Path):
        return path.expanduser()
    return Path(os.path.expanduser(os.path.expandvars(path))).expanduser()


async def _reply_to_chat(
    chat_id: int,
    text: str,
    *,
    reply_to: Optional[Message],
    disable_notification: bool = False,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[Any] = None,
) -> Optional[Message]:
    """向聊天发送消息，优先复用原消息上下文。"""

    if reply_to is not None:
        return await reply_to.answer(
            text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
        )

    bot = current_bot()

    async def _send() -> None:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
        )

    try:
        await _send_with_retry(_send)
    except TelegramBadRequest:
        raise
    return None


async def _send_session_ack(
    chat_id: int,
    session_path: Path,
    *,
    reply_to: Optional[Message],
) -> None:
    model_label = (ACTIVE_MODEL or "模型").strip() or "模型"
    session_id = session_path.stem if session_path else "unknown"
    prompt_message = (
        f"💭 {model_label}思考中，正在持续监听模型响应结果中。\n"
        f"sessionId : {session_id}"
    )
    ack_message = await _reply_to_chat(
        chat_id,
        prompt_message,
        reply_to=reply_to,
        disable_notification=True,
    )
    if ENABLE_PLAN_PROGRESS:
        CHAT_PLAN_MESSAGES.pop(chat_id, None)
        CHAT_PLAN_TEXT.pop(chat_id, None)
        CHAT_PLAN_COMPLETION.pop(chat_id, None)
    worker_log.info(
        "[session-map] chat=%s ack sent",
        chat_id,
        extra={
            **_session_extra(path=session_path),
            "ack_text": prompt_message,
        },
    )


async def _dispatch_prompt_to_model(
    chat_id: int,
    prompt: str,
    *,
    reply_to: Optional[Message],
    ack_immediately: bool = True,
) -> tuple[bool, Optional[Path]]:
    """统一处理向模型推送提示后的会话绑定、确认与监听。"""

    prev_watcher = CHAT_WATCHERS.pop(chat_id, None)
    if prev_watcher is not None:
        if not prev_watcher.done():
            prev_watcher.cancel()
            worker_log.info(
                "[session-map] chat=%s cancel previous watcher",
                chat_id,
                extra=_session_extra(),
            )
            try:
                await prev_watcher
            except asyncio.CancelledError:
                worker_log.info(
                    "[session-map] chat=%s previous watcher cancelled",
                    chat_id,
                    extra=_session_extra(),
                )
            except Exception as exc:  # noqa: BLE001
                worker_log.warning(
                    "[session-map] chat=%s previous watcher exited with error: %s",
                    chat_id,
                    exc,
                    extra=_session_extra(),
                )
        else:
            worker_log.debug(
                "[session-map] chat=%s previous watcher already done",
                chat_id,
                extra=_session_extra(),
            )
    session_path: Optional[Path] = None
    existing = CHAT_SESSION_MAP.get(chat_id)
    if existing:
        candidate = Path(existing)
        if candidate.exists():
            session_path = candidate
        else:
            CHAT_SESSION_MAP.pop(chat_id, None)
            _reset_delivered_hashes(chat_id, existing)
            _reset_delivered_offsets(chat_id, existing)
    else:
        _reset_delivered_hashes(chat_id)
        _reset_delivered_offsets(chat_id)

    pointer_path: Optional[Path] = None
    if CODEX_SESSION_FILE_PATH:
        pointer_path = resolve_path(CODEX_SESSION_FILE_PATH)

    if pointer_path is not None and session_path is None:
        session_path = _read_pointer_path(pointer_path)
        if session_path is not None:
            worker_log.info(
                "[session-map] chat=%s pointer -> %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )
    elif session_path is not None:
        worker_log.info(
            "[session-map] chat=%s reuse session %s",
            chat_id,
            session_path,
            extra=_session_extra(path=session_path),
        )

    target_cwd = CODEX_WORKDIR if CODEX_WORKDIR else None
    if pointer_path is not None:
        current_cwd = _read_session_meta_cwd(session_path) if session_path else None
        if session_path is None or (target_cwd and current_cwd != target_cwd):
            latest = _find_latest_rollout_for_cwd(pointer_path, target_cwd)
            if latest is not None:
                try:
                    SESSION_OFFSETS[str(latest)] = latest.stat().st_size
                except FileNotFoundError:
                    SESSION_OFFSETS[str(latest)] = 0
                _update_pointer(pointer_path, latest)
                session_path = latest
                worker_log.info(
                    "[session-map] chat=%s switch to cwd-matched %s",
                    chat_id,
                    session_path,
                    extra=_session_extra(path=session_path),
                )
        if _is_claudecode_model():
            fallback = _find_latest_claudecode_rollout(pointer_path)
            if fallback is not None and fallback != session_path:
                _update_pointer(pointer_path, fallback)
                session_path = fallback
                worker_log.info(
                    "[session-map] chat=%s fallback to ClaudeCode session %s",
                    chat_id,
                    session_path,
                    extra=_session_extra(path=session_path),
                )

    needs_session_wait = session_path is None
    if needs_session_wait and pointer_path is None:
        await _reply_to_chat(
            chat_id,
            f"未检测到 {MODEL_DISPLAY_LABEL} 会话日志，请稍后重试。",
            reply_to=reply_to,
        )
        return False, None

    try:
        tmux_send_line(TMUX_SESSION, prompt)
    except subprocess.CalledProcessError as exc:
        await _reply_to_chat(
            chat_id,
            f"tmux错误：{exc}",
            reply_to=reply_to,
        )
        return False, None

    if needs_session_wait:
        session_path = await _await_session_path(pointer_path, target_cwd)
        if session_path is None and pointer_path is not None and _is_claudecode_model():
            session_path = _find_latest_claudecode_rollout(pointer_path)
        if session_path is None:
            await _reply_to_chat(
                chat_id,
                f"未检测到 {MODEL_DISPLAY_LABEL} 会话日志，请稍后重试。",
                reply_to=reply_to,
            )
            return False, None
        if pointer_path is not None:
            _update_pointer(pointer_path, session_path)
            if _is_claudecode_model():
                worker_log.info(
                    "[session-map] chat=%s update ClaudeCode pointer -> %s",
                    chat_id,
                    session_path,
                    extra=_session_extra(path=session_path),
                )
        worker_log.info(
            "[session-map] chat=%s bind fresh session %s",
            chat_id,
            session_path,
            extra=_session_extra(path=session_path),
        )

    assert session_path is not None
    session_key = str(session_path)
    if session_key not in SESSION_OFFSETS:
        initial_offset = 0
        if session_path.exists():
            try:
                size = session_path.stat().st_size
            except FileNotFoundError:
                size = 0
            backtrack = max(SESSION_INITIAL_BACKTRACK_BYTES, 0)
            initial_offset = max(size - backtrack, 0)
        SESSION_OFFSETS[session_key] = initial_offset
        worker_log.info(
            "[session-map] init offset for %s -> %s",
            session_key,
            SESSION_OFFSETS[session_key],
            extra=_session_extra(key=session_key),
        )

    CHAT_SESSION_MAP[chat_id] = session_key
    _clear_last_message(chat_id)
    _reset_compact_tracking(chat_id)
    CHAT_FAILURE_NOTICES.pop(chat_id, None)
    worker_log.info(
        "[session-map] chat=%s bound to %s",
        chat_id,
        session_key,
        extra=_session_extra(key=session_key),
    )

    if ack_immediately:
        await _send_session_ack(chat_id, session_path, reply_to=reply_to)

    if SESSION_POLL_TIMEOUT > 0:
        start_time = time.monotonic()
        while time.monotonic() - start_time < SESSION_POLL_TIMEOUT:
            delivered = await _deliver_pending_messages(chat_id, session_path)
            if delivered:
                return True, session_path
            await asyncio.sleep(0.3)

    # 中断旧的延迟轮询（如果存在）
    await _interrupt_long_poll(chat_id)

    watcher_task = asyncio.create_task(
        _watch_and_notify(
            chat_id,
            session_path,
            max_wait=WATCH_MAX_WAIT,
            interval=WATCH_INTERVAL,
        )
    )
    CHAT_WATCHERS[chat_id] = watcher_task
    return True, session_path


async def _push_task_to_model(
    task: TaskRecord,
    *,
    chat_id: int,
    reply_to: Optional[Message],
    supplement: Optional[str],
    actor: Optional[str],
) -> tuple[bool, str, Optional[Path]]:
    """推送任务信息到模型，并附带补充描述。"""

    history_text, history_count = await _build_history_context_for_model(task.id)
    notes = await TASK_SERVICE.list_notes(task.id)
    prompt = _build_model_push_payload(
        task,
        supplement=supplement,
        history=history_text,
        notes=notes,
    )
    success, session_path = await _dispatch_prompt_to_model(
        chat_id,
        prompt,
        reply_to=reply_to,
        ack_immediately=False,
    )
    has_supplement = bool((supplement or "").strip())
    result_status = "success" if success else "failed"
    payload: dict[str, Any] = {
        "result": result_status,
        "has_supplement": has_supplement,
        "history_items": history_count,
        "history_chars": len(history_text),
        "prompt_chars": len(prompt),
        "model": ACTIVE_MODEL or "",
    }
    if has_supplement:
        payload["supplement"] = supplement or ""

    await _log_task_action(
        task.id,
        action="push_model",
        actor=actor,
        new_value=(supplement or "") if has_supplement else None,
        payload=payload,
    )
    if not success:
        worker_log.warning(
            "推送到模型失败：未能建立 Codex 会话",
            extra={"task_id": task.id},
        )
    else:
        worker_log.info(
            "已推送任务描述到模型",
            extra={
                "task_id": task.id,
                "status": task.status,
                "has_supplement": str(has_supplement),
            },
        )
    return success, prompt, session_path


def _extract_executable(cmd: str) -> Optional[str]:
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return None
    if not parts:
        return None
    return parts[0]


def _detect_environment_issues() -> tuple[list[str], Optional[Path]]:
    issues: list[str] = []
    workdir_raw = (os.environ.get("MODEL_WORKDIR") or CODEX_WORKDIR or "").strip()
    workdir_path: Optional[Path] = None
    if not workdir_raw:
        issues.append("未配置工作目录 (MODEL_WORKDIR)")
    else:
        candidate = resolve_path(workdir_raw)
        if not candidate.exists():
            issues.append(f"工作目录不存在: {workdir_raw}")
        elif not candidate.is_dir():
            issues.append(f"工作目录不是文件夹: {workdir_raw}")
        else:
            workdir_path = candidate

    try:
        tmux_bin()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        issues.append("未检测到 tmux，可通过 'brew install tmux' 安装")

    model_cmd = os.environ.get("MODEL_CMD")
    if not model_cmd and (ACTIVE_MODEL or "").lower() == "codex":
        model_cmd = os.environ.get("CODEX_CMD") or "codex"
    if model_cmd:
        executable = _extract_executable(model_cmd)
        if executable and shutil.which(executable) is None:
            issues.append(f"无法找到模型 CLI 可执行文件: {executable}")

    return issues, workdir_path


def _format_env_issue_message() -> str:
    if not ENV_ISSUES:
        return ""
    bullet_lines = []
    for issue in ENV_ISSUES:
        if "\n" in issue:
            first, *rest = issue.splitlines()
            bullet_lines.append(f"- {first}")
            bullet_lines.extend([f"  {line}" for line in rest])
        else:
            bullet_lines.append(f"- {issue}")
    return "当前 worker 环境存在以下问题，请先处理后再试：\n" + "\n".join(bullet_lines)


ENV_ISSUES, PRIMARY_WORKDIR = _detect_environment_issues()
if ENV_ISSUES:
    worker_log.error("环境自检失败: %s", "; ".join(ENV_ISSUES))

ROOT_DIR_ENV = os.environ.get("ROOT_DIR")
ROOT_DIR_PATH = Path(ROOT_DIR_ENV).expanduser() if ROOT_DIR_ENV else Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("TASKS_DATA_ROOT", ROOT_DIR_PATH / "data")).expanduser()
PROJECT_SLUG = (PROJECT_NAME or "default").replace("/", "-") or "default"
TASK_DB_PATH = DATA_ROOT / f"{PROJECT_SLUG}.db"
TASK_SERVICE = TaskService(TASK_DB_PATH, PROJECT_SLUG)

BOT_COMMANDS: list[tuple[str, str]] = [
    ("help", "查看全部命令"),
    ("tasks", "任务命令清单"),
    ("task_new", "创建任务"),
    ("task_list", "查看任务列表"),
    ("task_show", "查看任务详情"),
    ("task_update", "更新任务字段"),
    ("task_note", "添加任务备注"),
]

COMMAND_KEYWORDS: set[str] = {command for command, _ in BOT_COMMANDS}
COMMAND_KEYWORDS.update({"task_child", "task_children", "task_delete"})

WORKER_MENU_BUTTON_TEXT = "📋 任务列表"
WORKER_CREATE_TASK_BUTTON_TEXT = "➕ 创建任务"

TASK_ID_VALID_PATTERN = re.compile(r"^TASK_[A-Z0-9_]+$")
TASK_ID_USAGE_TIP = "任务 ID 格式无效，请使用 TASK_0001"


def _build_worker_main_keyboard() -> ReplyKeyboardMarkup:
    """Worker 端常驻键盘，提供任务列表入口。"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=WORKER_MENU_BUTTON_TEXT),
                KeyboardButton(text=WORKER_CREATE_TASK_BUTTON_TEXT),
            ]
        ],
        resize_keyboard=True,
    )


def _resolve_worker_target_chat_ids() -> List[int]:
    """收集需要推送菜单的 chat id，优先使用状态文件记录。"""
    targets: set[int] = set()

    def _append(value: Optional[int]) -> None:
        if value is None:
            return
        targets.add(value)

    for env_name in ("WORKER_CHAT_ID", "ALLOWED_CHAT_ID"):
        raw = os.environ.get(env_name)
        if raw:
            stripped = raw.strip()
            if stripped.isdigit():
                _append(int(stripped))

    state_file = os.environ.get("STATE_FILE")
    if state_file:
        path = Path(state_file).expanduser()
        try:
            raw_state = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            worker_log.debug("STATE_FILE 不存在，跳过菜单推送来源", extra=_session_extra(key="state_file_missing"))
        except json.JSONDecodeError as exc:
            worker_log.warning("STATE_FILE 解析失败：%s", exc, extra=_session_extra(key="state_file_invalid"))
        else:
            if isinstance(raw_state, dict):
                entry = raw_state.get(PROJECT_SLUG) or raw_state.get(PROJECT_NAME)
                if isinstance(entry, dict):
                    chat_val = entry.get("chat_id")
                    if isinstance(chat_val, int):
                        _append(chat_val)
                    elif isinstance(chat_val, str) and chat_val.isdigit():
                        _append(int(chat_val))

    config_path_env = os.environ.get("MASTER_PROJECTS_PATH")
    config_path = Path(config_path_env).expanduser() if config_path_env else ROOT_DIR_PATH / "config/projects.json"
    try:
        configs_raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        worker_log.debug("未找到项目配置 %s，跳过 allowed_chat_id", config_path, extra=_session_extra(key="projects_missing"))
    except json.JSONDecodeError as exc:
        worker_log.warning("项目配置解析失败：%s", exc, extra=_session_extra(key="projects_invalid"))
    else:
        if isinstance(configs_raw, list):
            for item in configs_raw:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("project_slug") or "").strip()
                bot_name = str(item.get("bot_name") or "").strip()
                if slug != PROJECT_SLUG and bot_name != PROJECT_NAME:
                    continue
                allowed_val = item.get("allowed_chat_id")
                if isinstance(allowed_val, int):
                    _append(allowed_val)
                elif isinstance(allowed_val, str) and allowed_val.strip().isdigit():
                    _append(int(allowed_val.strip()))

    return sorted(targets)


def _auto_record_chat_id(chat_id: int) -> None:
    """首次收到消息时自动将 chat_id 记录到 state 文件。

    仅在以下条件同时满足时写入：
    1. STATE_FILE 环境变量已配置
    2. state 文件存在
    3. 当前项目在 state 中的 chat_id 为空
    """
    state_file_env = os.environ.get("STATE_FILE")
    if not state_file_env:
        return

    state_path = Path(state_file_env).expanduser()
    if not state_path.exists():
        worker_log.debug(
            "STATE_FILE 不存在，跳过自动记录 chat_id",
            extra={**_session_extra(), "path": str(state_path)},
        )
        return

    # 使用文件锁保证并发安全
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")
    import fcntl

    try:
        with open(lock_path, "w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            try:
                # 读取当前 state
                raw_state = json.loads(state_path.read_text(encoding="utf-8"))
                if not isinstance(raw_state, dict):
                    worker_log.warning(
                        "STATE_FILE 格式异常，跳过自动记录",
                        extra=_session_extra(),
                    )
                    return

                # 检查当前项目的 chat_id
                project_key = PROJECT_SLUG or PROJECT_NAME
                if not project_key:
                    worker_log.warning(
                        "PROJECT_SLUG 和 PROJECT_NAME 均未设置，跳过自动记录",
                        extra=_session_extra(),
                    )
                    return

                project_state = raw_state.get(project_key)
                if not isinstance(project_state, dict):
                    # 项目不存在，创建新条目
                    raw_state[project_key] = {
                        "chat_id": chat_id,
                        "model": ACTIVE_MODEL or "codex",
                        "status": "running",
                    }
                    need_write = True
                elif project_state.get("chat_id") is None:
                    # chat_id 为空，更新
                    project_state["chat_id"] = chat_id
                    need_write = True
                else:
                    # chat_id 已存在，无需更新
                    need_write = False

                if need_write:
                    # 写入更新后的 state
                    tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
                    tmp_path.write_text(
                        json.dumps(raw_state, ensure_ascii=False, indent=4),
                        encoding="utf-8",
                    )
                    tmp_path.replace(state_path)
                    worker_log.info(
                        "已自动记录 chat_id=%s 到 state 文件",
                        chat_id,
                        extra={**_session_extra(), "project": project_key},
                    )
                else:
                    worker_log.debug(
                        "chat_id 已存在，跳过自动记录",
                        extra={**_session_extra(), "existing_chat_id": project_state.get("chat_id")},
                    )

            except json.JSONDecodeError as exc:
                worker_log.error(
                    "STATE_FILE 解析失败，跳过自动记录：%s",
                    exc,
                    extra=_session_extra(),
                )
            except Exception as exc:
                worker_log.error(
                    "自动记录 chat_id 失败：%s",
                    exc,
                    extra={**_session_extra(), "chat": chat_id},
                )
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception as exc:
        worker_log.error(
            "获取文件锁失败：%s",
            exc,
            extra=_session_extra(),
        )
    finally:
        # 清理锁文件
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass


async def _broadcast_worker_keyboard(bot: Bot) -> None:
    """启动时主动推送菜单，确保 Telegram 键盘同步。"""
    targets = _resolve_worker_target_chat_ids()
    if not targets:
        worker_log.info("无可推送的聊天，跳过菜单广播", extra=_session_extra())
        return
    for chat_id in targets:
        try:
            text, inline_markup = await _build_task_list_view(status=None, page=1, limit=DEFAULT_PAGE_SIZE)
        except Exception as exc:
            worker_log.error(
                "构建任务列表失败：%s",
                exc,
                extra={**_session_extra(), "chat": chat_id},
            )
            continue

        parse_mode = _parse_mode_value()
        prepared = _prepare_model_payload(text)

        async def _send_formatted(payload: str) -> None:
            await bot.send_message(
                chat_id=chat_id,
                text=payload,
                parse_mode=parse_mode,
                reply_markup=inline_markup,
            )

        async def _send_raw(payload: str) -> None:
            await bot.send_message(
                chat_id=chat_id,
                text=payload,
                parse_mode=None,
                reply_markup=inline_markup,
            )

        try:
            delivered = await _send_with_markdown_guard(
                prepared,
                _send_formatted,
                raw_sender=_send_raw,
            )
        except TelegramForbiddenError as exc:
            worker_log.warning("推送任务列表被拒绝：%s", exc, extra={**_session_extra(), "chat": chat_id})
        except TelegramBadRequest as exc:
            worker_log.warning("推送任务列表失败：%s", exc, extra={**_session_extra(), "chat": chat_id})
        except (TelegramRetryAfter, TelegramNetworkError) as exc:
            worker_log.error("推送任务列表网络异常：%s", exc, extra={**_session_extra(), "chat": chat_id})
            await _notify_send_failure_message(chat_id)
        except Exception as exc:
            worker_log.error("推送任务列表异常：%s", exc, extra={**_session_extra(), "chat": chat_id})
        else:
            worker_log.info(
                "已推送任务列表至 chat_id=%s",
                chat_id,
                extra={**_session_extra(), "length": str(len(delivered))},
            )

STATUS_LABELS = {
    "research": "🔍 调研中",
    "test": "🧪 测试中",
    "done": "✅ 已完成",
}

NOTE_LABELS = {
    "research": "调研",
    "test": "测试",
    "bug": "缺陷",
    "misc": "其他",
}

TASK_TYPE_LABELS = {
    "requirement": "需求",
    "defect": "缺陷",
    "task": "优化",
    "risk": "风险",
}

TASK_TYPE_EMOJIS = {
    "requirement": "📌",
    "defect": "🐞",
    "task": "🛠️",
    "risk": "⚠️",
}

HISTORY_FIELD_LABELS = {
    "title": "标题",
    "status": "状态",
    "priority": "优先级",
    "description": "描述",
    "due_date": "截止时间",
    "task_type": "类型",
    "type": "类型",
    "tags": "标签",
    "assignee": "负责人",
    "parent_id": "父任务",
    "root_id": "根任务",
    "archived": "归档状态",
    "create": "创建任务",
}

_TASK_TYPE_ALIAS: dict[str, str] = {}
for _code, _label in TASK_TYPE_LABELS.items():
    _TASK_TYPE_ALIAS[_code] = _code
    _TASK_TYPE_ALIAS[_code.lower()] = _code
    _TASK_TYPE_ALIAS[_label] = _code
    _TASK_TYPE_ALIAS[_label.lower()] = _code
_TASK_TYPE_ALIAS.update(
    {
        "req": "requirement",
        "需求": "requirement",
        "feature": "requirement",
        "story": "requirement",
        "bug": "defect",
        "issue": "defect",
        "缺陷": "defect",
        "任务": "task",
        "risk": "risk",
        "风险": "risk",
    }
)

_STATUS_ALIAS_MAP: dict[str, str] = {key.lower(): value for key, value in STATUS_ALIASES.items()}

SKIP_TEXT = "跳过"
TASK_LIST_CREATE_CALLBACK = "task:list_create"
TASK_LIST_SEARCH_CALLBACK = "task:list_search"
TASK_LIST_SEARCH_PAGE_CALLBACK = "task:list_search_page"
TASK_LIST_RETURN_CALLBACK = "task:list_return"
TASK_DETAIL_BACK_CALLBACK = "task:detail_back"
TASK_HISTORY_PAGE_CALLBACK = "task:history_page"
TASK_HISTORY_BACK_CALLBACK = "task:history_back"
TASK_DESC_INPUT_CALLBACK = "task:desc_input"
TASK_DESC_CLEAR_CALLBACK = "task:desc_clear"
TASK_DESC_CONFIRM_CALLBACK = "task:desc_confirm"
TASK_DESC_RETRY_CALLBACK = "task:desc_retry"
TASK_DESC_CANCEL_CALLBACK = "task:desc_cancel"
TASK_DESC_CLEAR_TEXT = "🗑️ 清空描述"
TASK_DESC_CANCEL_TEXT = "❌ 取消"
TASK_DESC_REPROMPT_TEXT = "✏️ 重新打开输入提示"
TASK_DESC_CONFIRM_TEXT = "✅ 确认更新"
TASK_DESC_RETRY_TEXT = "✏️ 重新输入"

DESCRIPTION_MAX_LENGTH = 3000
SEARCH_KEYWORD_MIN_LENGTH = 2
SEARCH_KEYWORD_MAX_LENGTH = 100
RESEARCH_DESIGN_STATUSES = {"research"}

HISTORY_EVENT_FIELD_CHANGE = "field_change"
HISTORY_EVENT_TASK_ACTION = "task_action"
HISTORY_EVENT_MODEL_REPLY = "model_reply"
HISTORY_EVENT_MODEL_SUMMARY = "model_summary"
HISTORY_DISPLAY_VALUE_LIMIT = 200
HISTORY_MODEL_REPLY_LIMIT = 1200
HISTORY_MODEL_SUMMARY_LIMIT = 1600
MODEL_REPLY_PAYLOAD_LIMIT = 4000
MODEL_SUMMARY_PAYLOAD_LIMIT = 4000
MODEL_HISTORY_MAX_ITEMS = 50
MODEL_HISTORY_MAX_CHARS = 4096
TASK_HISTORY_PAGE_SIZE = 6
HISTORY_TRUNCATION_NOTICE = "⚠️ 本页部分记录因 Telegram 长度限制已截断，建议导出历史查看完整内容。"
HISTORY_TRUNCATION_NOTICE_SHORT = "⚠️ 本页已截断"

_NUMBER_PREFIX_RE = re.compile(r"^\d+\.\s")


def _format_numbered_label(index: int, label: str) -> str:
    text = label or ""
    if _NUMBER_PREFIX_RE.match(text):
        return text
    return f"{index}. {text}" if text else f"{index}."


def _number_inline_buttons(rows: list[list[InlineKeyboardButton]], *, start: int = 1) -> None:
    """仅用于 FSM 交互的 inline 按钮，添加数字前缀以便键盘选择。"""
    counter = start
    for row in rows:
        for button in row:
            button.text = _format_numbered_label(counter, button.text or "")
            counter += 1


def _number_reply_buttons(rows: list[list[KeyboardButton]], *, start: int = 1) -> None:
    """仅用于 FSM 交互的 reply 按钮，添加数字前缀便于输入。"""
    counter = start
    for row in rows:
        for button in row:
            button.text = _format_numbered_label(counter, button.text or "")
            counter += 1


def _strip_number_prefix(value: Optional[str]) -> str:
    if not value:
        return ""
    return _NUMBER_PREFIX_RE.sub("", value, count=1).strip()


def _normalize_choice_token(value: Optional[str]) -> str:
    """统一处理按钮输入文本，移除序号并规范大小写。"""

    if value is None:
        return ""
    stripped = _strip_number_prefix(value)
    return stripped.strip()


def _is_skip_message(value: Optional[str]) -> bool:
    """判断用户是否选择了跳过。"""

    token = _normalize_choice_token(value).lower()
    return token in {SKIP_TEXT.lower(), "skip"}


def _is_cancel_message(value: Optional[str]) -> bool:
    """判断用户是否输入了取消指令。"""

    token = _normalize_choice_token(value)
    if not token:
        return False
    lowered = token.lower()
    cancel_tokens = {"取消", "cancel", "quit"}
    # 兼容含有表情的菜单按钮文本，避免用户需重复点击取消。
    cancel_tokens.add(_normalize_choice_token(TASK_DESC_CANCEL_TEXT).lower())
    return lowered in cancel_tokens


_MARKDOWN_ESCAPE_RE = re.compile(r"([_*\[\]()~`>#+=|{}.!])")
TASK_REFERENCE_PATTERN = re.compile(r"/?TASK[_]?\d{4,}")


def _escape_markdown_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    text = text.replace("\\", "\\\\")
    return _MARKDOWN_ESCAPE_RE.sub(r"\\\1", text)


def _resolve_reply_choice(
    value: Optional[str],
    *,
    options: Sequence[str],
) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        return ""
    stripped = _strip_number_prefix(trimmed)
    for candidate in (trimmed, stripped):
        if candidate in options:
            return candidate
    for candidate in (trimmed, stripped):
        if candidate.isdigit():
            index = int(candidate) - 1
            if 0 <= index < len(options):
                return options[index]
    return stripped


def _status_display_order() -> tuple[str, ...]:
    """返回状态展示顺序，保持与任务状态定义一致。"""

    return tuple(TASK_STATUSES)


STATUS_DISPLAY_ORDER: tuple[str, ...] = _status_display_order()
STATUS_FILTER_OPTIONS: tuple[Optional[str], ...] = (None, *STATUS_DISPLAY_ORDER)

VIBE_PHASE_BODY = """## 需求调研问题分析阶段 - 严禁修改文件｜允许访问网络｜自定义扫描范围
以上是任务和背景描述，你是一名专业的全栈工程师，使用尽可能多的专业 agents，产出调研结论：给出实现思路、方案优劣与决策选项；
重要约束：
- 响应的内容以及思考过程都始终使用简体中文回复，在 CLI 终端中用格式化后的 markdown 的格式来呈现数据，禁止使用 markdown 表格，流程图的话改用纯文本绘制，markdown 中的代码、流程等有必要的内容需要使用围栏代码块。
- 先通读项目：厘清部署架构、系统架构、代码风格与通用组件；不确定时先提问再推进。
- 充分分析，详细讨论清楚需求以及可能发送的边缘场景，列出需我确认的关键决策点；不明之处及时澄清。
- 使用 Task 工具时必须标注：RESEARCH ONLY - NO FILE MODIFICATIONS。
- 可调用所需的 tools / subAgent / MCP 等一切辅助工具调研，本地没有的时候自己上网找文档安装。
- 涉及开发设计时，明确依赖、数据库表与字段、伪代码与影响范围，按生产级别的安全、性能、高可用等标准考虑。
- 制定方案：列出至少两种可选的思路，比较其优缺点后推荐最佳方案。
- 需要用户做出决策或待用户确认时，给出待决策项的纯数字编号以及 ABCD 的选项，方便用户回复你。
- com.hypha.infra 包相关的源码在/Users/david/hypha/infra 目录下，需要时可进行查看或修改
- 自行整理出本次会话的 checklist ，防止在后续的任务执行中遗漏。
- 最后列出本次使用的模型、MCP、Tools、subAgent 及 token 消耗； ultrathink"""

TEST_PHASE_REQUIREMENTS = """## 测试阶段（可改文件｜可联网｜自定义扫描范围）
以上是任务和任务描述，你是一名专业全栈工程师，使用尽可能多的专业 agents，在终端一次性跑完前后端测试（与该任务相关的代码），覆盖：单元、集成契约、API/数据交互、冒烟、端到端（后端视角）、性能压力、并发正确性（可选）、安全与依赖漏洞、覆盖率统计与阈值校验；最终产出报告与待确认修复清单。IMPLEMENTATION APPROVED

### 全局约定
- 工具与依赖：缺失即联网安装；优先 use context7（如无则自动安装，可用 chrome-devtools-mcp）。
- 仅在**当前仓库**内操作；遵循现有代码风格与 lint；最小化改动。
- 统一输出：HTML/文本报告、Trace/Video/Screenshot、覆盖率阈值硬闸可配置。

### 后端
- 构建与运行：所有 Maven 命令用 `./mvnw`；启动附加参数：
  -Dspring-boot.run.profiles=dev -Dspring-boot.run.jvmArguments="-javaagent:/Users/david/devops/opentelemetry-javaagent.jar -Dotel.service.name=main-application -Dotel.traces.exporter=none -Dotel.metrics.exporter=none -Dotel.logs.exporter=none"
- 测试基线：若无用例，按生产标准为各层（Controller/Service/Repository）与每个 REST API 生成丰富完整的 JUnit 5 + Spring 测试与集成用例。
- 生态与规范：若缺失则安装并配置——JUnit 5、Mockito、Testcontainers、JaCoCo、JMeter、Checkstyle。
- 冒烟：对健康检查与关键 API 做 200/超时鉴权三类断言（健康检查为 `/health/check`），生成 JaCoCo 并按行分支阈值硬闸。
- 性能负载：在压力场景下给出系统当前可承受的关键边界指标。
- 并发正确性（可选）：高风险类用 JMH（微基准）与 jcstress（可见性原子性）抽样验证。
- 变更策略：明显低风险且确定性高的问题直接修（选择器等待策略不稳 Mock/可复现小缺陷）；高风险变更列清单与建议，待确认后再改。

### 前端（Playwright）
- 目标：跨浏览器（Chromium/Firefox/WebKit）与品牌兼容；E2E/冒烟功能交互/UI 可视回归（`toHaveScreenshot`）；接口与数据交互（拦截/Mock/HAR 回放）；网络失败与重试；移动端环境模拟（iPhone/Android 视口、触摸、定位时区、慢网离线）。
- 性能：采集 Navigation/Resource Timing；（可选）如检测到 Lighthouse 依赖则对首页关键路由跑桌面移动审计并输出 JSON/HTML 与阈值告警。
- 执行策略（按序，压缩版）：
  1) 安装校验 Playwright 依赖与三大浏览器二进制（仅当前项目）。
  2) 生成校验 `playwright.config.ts`（chromium/firefox/webkit + Desktop Chrome/iPhone14/Pixel7；全局 `trace: retain-on-failure, video: retain-on-failure, screenshot: only-on-failure`）；无基线则首次运行生成快照基线（记录为“基线生成”而非失败）。
  3) 冒烟优先：仅跑主流程用例（可按 `tests/e2e/**/smoke*.spec.ts` 约定），收集 `console.error/requestfailed`，并将任何错误计入报告。
  4) 全量回归：按“Project”维度并行跑：三大浏览器 + 两款移动设备；UI 测试对关键页面与组件使用 `toHaveScreenshot`；对动态区域应用 mask/threshold 以减少抖动；交互与接口使用 `route()` 进行定向 Mock 与异常场景注入；必要时使用 HAR 回放；模拟慢 3G、离线、地理位置、时区、深/浅色模式、权限（通知/定位）。
  5) 性能小节：汇总 Web Performance API 指标（如 FCP/LCP/TBT/TTFB 可得时）并输出到报告；如检测到 lighthouse 依赖，对首页/关键路由跑 Lighthouse（桌面/移动各一次），输出 JSON/HTML 报告与阈值告警。
  6) 结果汇总（文本表）
    | 维度 | 浏览器/设备 | 用例数 | 失败 | 重跑后 | 截图 Diff | 性能阈值告警 | 备注 |
    |---|---|---:|---:|---:|---:|---:|---|
  7) 自动最小化修复（仅限安全改动）
    - 分类：用例问题/测试夹具问题/应用真实缺陷
    - 对“明显低风险且确定性高”的问题直接修复（如选择器失效、等待策略、Mock 不稳、易复现前端异常的局部修正）；
    - 修复后**本地自测**：新增/更新最少 10 条测试输入（正常/边界/异常）与预期，并复跑相关项目
    - 产出：变更清单（文件/函数/影响面）、回滚命令、后续观察项
  8) 高风险的改动记录为清单并给出修改建议等，最后所有任务执行完成后，由我确认是否需要修复
    - 如“是否引入/更新 lighthouse、是否提高视觉阈值、是否纳入 WebKit 移动模拟”等

### 输出顺序（严格执行）
A. 背景与假设（含不确定项）  
B. 预检结果与配置要点  
C. 冒烟与全量汇总表 + 关键失败 TopN（含直链到 Trace）  
D. 性能摘录（及阈值对比）  
E. 自动修复的变更清单（含回滚说明）与自测用例×≥10  
F. 仍需我确认的决策点  
- 最后列出本次使用的模型、MCP、Tools、subAgent、token 消耗以及执行耗时；ultrathink"""

MODEL_PUSH_CONFIG: dict[str, dict[str, Any]] = {
    "research": {
        "include_task_info": True,
        "body": VIBE_PHASE_BODY,
    },
    "test": {
        "include_task_info": True,
        "body": VIBE_PHASE_BODY,
    },
    "done": {
        "include_task_info": False,
        "body": "/compact",
    },
}

MODEL_PUSH_ELIGIBLE_STATUSES: set[str] = set(MODEL_PUSH_CONFIG)
MODEL_PUSH_SUPPLEMENT_STATUSES: set[str] = {
    "research",
    "test",
}

SUMMARY_COMMAND_PREFIX = "/task_summary_request_"
SUMMARY_COMMAND_ALIASES: tuple[str, ...] = (
    "/task_summary_request_",
    "/tasksummaryrequest",
)


LEGACY_BUG_HISTORY_HEADER = "缺陷记录（最近 3 条）"


def _strip_legacy_bug_header(text: str) -> str:
    """移除历史模板遗留的缺陷标题，防止提示词重复。"""

    if not text:
        return ""
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        token = line.strip()
        if token and token.startswith(LEGACY_BUG_HISTORY_HEADER):
            # 兼容旧模板形式，如“缺陷记录（最近 3 条） -”或带冒号的写法
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _build_model_push_payload(
    task: TaskRecord,
    supplement: Optional[str] = None,
    history: Optional[str] = None,
    notes: Optional[Sequence[TaskNoteRecord]] = None,
) -> str:
    """根据任务状态构造推送到 tmux 的指令。"""

    config = MODEL_PUSH_CONFIG.get(task.status)
    if config is None:
        raise ValueError(f"状态 {task.status!r} 未配置推送模板")

    body = config.get("body", "")
    include_task = bool(config.get("include_task_info"))
    body = (body or "").strip()
    history_block = (history or "").strip()
    status = task.status

    if status in {"research", "test"}:
        body = ""

    if "{history}" in body:
        replacement = history_block or "（暂无任务执行记录）"
        body = body.replace("{history}", replacement).strip()
        history_block = ""

    supplement_text = (supplement or "").strip()
    segments: list[str] = []

    notes = notes or ()
    regular_notes: list[str] = []

    for note in notes:
        content = note.content or ""
        if not content.strip():
            continue
        summarized = _summarize_note_text(content)
        if note.note_type == "bug":
            # 缺陷备注不再拼接到推送提示词中，避免与任务执行记录重复
            continue
        regular_notes.append(summarized)

    task_code_plain = f"/{task.id}" if task.id else "-"

    if include_task and status in {"research", "test"}:
        phase_line = VIBE_PHASE_PROMPT
        title = (task.title or "").strip() or "-"
        description = (task.description or "").strip() or "-"
        supplement_value = supplement_text or "-"
        note_text = "；".join(regular_notes) if regular_notes else "-"

        lines: list[str] = [
            phase_line,
            f"任务标题：{title}",
            f"任务编码：{task_code_plain}",
            f"任务描述：{description}",
            f"任务备注：{note_text}",
            f"补充任务描述：{supplement_value}",
            "",
        ]
        history_intro = "以下为任务执行记录，用于辅助回溯任务处理记录："
        if history_block:
            lines.append(history_intro)
            lines.extend(history_block.splitlines())
        else:
            lines.append(f"{history_intro} -")
        return _strip_legacy_bug_header("\n".join(lines))
    else:
        # 非上述状态维持旧逻辑，避免影响完成等场景
        info_lines: list[str] = []
        if include_task:
            title = (task.title or "-").strip() or "-"
            description = (task.description or "").strip() or "暂无"
            supplement_value = supplement_text or "-"
            info_lines.extend(
                [
                    f"任务标题：{title}",
                    f"任务编码：{task_code_plain}",
                    f"任务描述：{description}",
                    f"补充任务描述：{supplement_value}",
                ]
            )
        elif supplement_text:
            info_lines.append(f"补充任务描述：{supplement_text}")

        if history_block:
            if info_lines and info_lines[-1].strip():
                info_lines.append("")
            info_lines.append("任务执行记录：")
            info_lines.append(history_block)

        if info_lines:
            info_segment = "\n".join(info_lines)
            if info_segment.strip():
                segments.append(info_segment)

    if body:
        segments.append(body)

    tail_prompt = ""
    if status in {"research", "test"}:
        tail_prompt = VIBE_PHASE_PROMPT

    result = "\n\n".join(segment for segment in segments if segment)
    if tail_prompt:
        if result:
            result = f"{result}\n{tail_prompt}"
        else:
            result = tail_prompt
    return _strip_legacy_bug_header(result or body)


try:
    SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
except ZoneInfoNotFoundError:
    SHANGHAI_TZ = None


def _normalize_task_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    token_raw = value.strip()
    if not token_raw:
        return None
    token = token_raw[1:] if token_raw.startswith("/") else token_raw
    candidate = token.split()[0]
    if "@" in candidate:
        candidate = candidate.split("@", 1)[0]
    if candidate.lower() in COMMAND_KEYWORDS:
        return None
    normalized = TaskService._convert_task_id_token(candidate.upper())
    if not normalized or not normalized.startswith("TASK_"):
        return None
    if not TASK_ID_VALID_PATTERN.fullmatch(normalized):
        return None
    return normalized


def _format_task_command(task_id: str) -> str:
    """根据当前 parse_mode 输出可点击的任务命令文本。"""

    command = f"/{task_id}"
    if _IS_MARKDOWN and not _IS_MARKDOWN_V2:
        return command.replace("_", r"\_")
    return command


def _wrap_text_in_code_block(text: str) -> tuple[str, str]:
    """将推送消息包装为 Telegram 代码块，并返回渲染文本与 parse_mode。"""

    if MODEL_OUTPUT_PARSE_MODE == ParseMode.HTML:
        escaped = html.escape(text, quote=False)
        return f"<pre><code>{escaped}</code></pre>", ParseMode.HTML.value
    if MODEL_OUTPUT_PARSE_MODE == ParseMode.MARKDOWN_V2:
        escaped = text.replace("\\", "\\\\").replace("`", "\\`")
        return f"```\n{escaped}\n```", ParseMode.MARKDOWN_V2.value
    # 默认退回 Telegram Markdown，保证代码块高亮可用
    return f"```\n{text}\n```", ParseMode.MARKDOWN.value


async def _reply_task_detail_message(message: Message, task_id: str) -> None:
    try:
        detail_text, markup = await _render_task_detail(task_id)
    except ValueError:
        await _answer_with_markdown(message, f"任务 {task_id} 不存在")
        return
    await _answer_with_markdown(message, detail_text, reply_markup=markup)


def _format_local_time(value: Optional[str]) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if SHANGHAI_TZ is None:
        return dt.strftime("%Y-%m-%d %H:%M")
    try:
        return dt.astimezone(SHANGHAI_TZ).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return dt.strftime("%Y-%m-%d %H:%M")


def _canonical_status_token(value: Optional[str], *, quiet: bool = False) -> Optional[str]:
    if value is None:
        return None
    token = value.strip().lower()
    mapped = _STATUS_ALIAS_MAP.get(token, token)
    if mapped not in TASK_STATUSES:
        if not quiet:
            worker_log.warning("检测到未知任务状态：%s", value)
        return token
    if mapped != token and not quiet:
        worker_log.info("任务状态别名已自动转换：%s -> %s", token, mapped)
    return mapped


def _format_status(status: str) -> str:
    canonical = _canonical_status_token(status)
    if canonical and canonical in STATUS_LABELS:
        return STATUS_LABELS[canonical]
    return status


def _status_icon(status: Optional[str]) -> str:
    """提取状态对应的 emoji 图标，用于紧凑展示。"""

    if not status:
        return ""
    canonical = _canonical_status_token(status, quiet=True)
    if not canonical:
        return ""
    label = STATUS_LABELS.get(canonical)
    if not label:
        return ""
    first_token = label.split(" ", 1)[0]
    if not first_token:
        return ""
    # 避免把纯文字当图标
    if first_token[0].isalnum():
        return ""
    return first_token


def _strip_task_type_emoji(value: str) -> str:
    """去除前缀的任务类型 emoji，保持其余文本原样。"""

    trimmed = value.strip()
    for emoji in TASK_TYPE_EMOJIS.values():
        if trimmed.startswith(emoji):
            return trimmed[len(emoji):].strip()
    return trimmed


def _format_task_type(task_type: Optional[str]) -> str:
    if not task_type:
        return "⚪ 未设置"
    label = TASK_TYPE_LABELS.get(task_type, task_type)
    icon = TASK_TYPE_EMOJIS.get(task_type)
    if icon:
        return f"{icon} {label}"
    return label


def _format_note_type(note_type: str) -> str:
    return NOTE_LABELS.get(note_type, note_type)


def _format_priority(priority: int) -> str:
    priority = max(1, min(priority, 5))
    return f"P{priority}"


def _status_filter_label(value: Optional[str]) -> str:
    if value is None:
        return "⭐ 全部"
    canonical = _canonical_status_token(value)
    if canonical and canonical in STATUS_LABELS:
        return STATUS_LABELS[canonical]
    return value


def _build_status_filter_row(current_status: Optional[str], limit: int) -> list[list[InlineKeyboardButton]]:
    """构造任务列表顶部的状态筛选按钮，并根据数量动态换行。"""

    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    options = list(STATUS_FILTER_OPTIONS)
    row_capacity = 3
    if len(options) <= 4:
        row_capacity = max(len(options), 1)
    for option in options:
        base_label = _status_filter_label(option)
        label = f"✔️ {base_label}" if option == current_status else base_label
        token = option or "-"
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"task:list_page:{token}:1:{limit}",
            )
        )
        if len(row) == row_capacity:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows



def _format_task_list_entry(task: TaskRecord) -> str:
    indent = "  " * max(task.depth, 0)
    title_raw = (task.title or "").strip()
    # 修复：避免双重转义
    if not title_raw:
        title = "-"
    elif _IS_MARKDOWN_V2:
        title = title_raw
    else:
        title = _escape_markdown_text(title_raw)
    type_icon = TASK_TYPE_EMOJIS.get(task.task_type)
    if not type_icon:
        type_icon = "⚪"
    return f"{indent}- {type_icon} {title}"


def _compose_task_button_label(task: TaskRecord, *, max_length: int = 60) -> str:
    """生成任务列表按钮文本，将状态图标置于最左侧，保证两类图标都保留。"""

    title_raw = (task.title or "").strip()
    title = title_raw if title_raw else "-"
    type_icon = TASK_TYPE_EMOJIS.get(task.task_type) or "⚪"
    status_icon = _status_icon(task.status)

    # 按“状态 → 类型”的顺序拼接前缀，让用户先看到进度状态。
    prefix_parts: list[str] = []
    if status_icon:
        prefix_parts.append(status_icon)
    if type_icon:
        prefix_parts.append(type_icon)
    prefix = " ".join(prefix_parts)
    if prefix:
        prefix = f"{prefix} "

    available = max_length - len(prefix)
    if available <= 0:
        truncated_title = "…"
    else:
        if len(title) > available:
            if available <= 1:
                truncated_title = "…"
            else:
                truncated_title = title[: available - 1] + "…"
        else:
            truncated_title = title

    label = f"{prefix}{truncated_title}" if prefix else truncated_title
    if len(label) > max_length:
        label = label[: max_length - 1] + "…"
    return label


def _format_task_detail(
        task: TaskRecord,
        *,
        notes: Sequence[TaskNoteRecord],
    ) -> str:
    # 修复：仅在非 MarkdownV2 模式下手动转义，避免双重转义
    # MarkdownV2 模式下由 _prepare_model_payload() 统一处理转义
    title_raw = (task.title or "").strip()
    if _IS_MARKDOWN_V2:
        title_text = title_raw if title_raw else "-"
    else:
        title_text = _escape_markdown_text(title_raw) if title_raw else "-"

    task_id_text = _format_task_command(task.id)
    lines: list[str] = [
        f"📝 标题：{title_text}",
        f"🏷️ 任务编码：{task_id_text}",
        f"⚙️ 状态：{_format_status(task.status)}",
        f"🚦 优先级：{_format_priority(task.priority)}",
        f"📂 类型：{_format_task_type(task.task_type)}",
    ]

    # 修复：描述字段也避免双重转义
    description_raw = task.description or "暂无"
    if _IS_MARKDOWN_V2:
        description_text = description_raw
    else:
        description_text = _escape_markdown_text(description_raw)

    lines.append(f"🖊️ 描述：{description_text}")
    lines.append(f"📅 创建时间：{_format_local_time(task.created_at)}")
    lines.append(f"🔁 更新时间：{_format_local_time(task.updated_at)}")

    # 修复：父任务ID字段也避免双重转义
    if task.parent_id:
        if _IS_MARKDOWN_V2:
            parent_text = task.parent_id
        else:
            parent_text = _escape_markdown_text(task.parent_id)
        lines.append(f"👪 父任务：{parent_text}")

    return "\n".join(lines)


def _parse_history_payload(payload_raw: Optional[str]) -> dict[str, Any]:
    if not payload_raw:
        return {}
    try:
        data = json.loads(payload_raw)
    except json.JSONDecodeError:
        worker_log.warning("历史 payload 解析失败：%s", payload_raw, extra=_session_extra())
        return {}
    if isinstance(data, dict):
        return data
    worker_log.warning("历史 payload 类型异常：%s", type(data), extra=_session_extra())
    return {}


def _trim_history_value(value: Optional[str], limit: int = HISTORY_DISPLAY_VALUE_LIMIT) -> str:
    if value is None:
        return "-"
    text = normalize_newlines(str(value)).strip()
    if not text:
        return "-"
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _history_field_label(field: Optional[str]) -> str:
    """返回历史字段的中文标签。"""

    token = (field or "").strip().lower()
    if not token:
        return "字段"
    return HISTORY_FIELD_LABELS.get(token, token)


def _format_history_value(field: Optional[str], value: Optional[str]) -> str:
    """将字段值转为更易读的文本。"""

    text = _trim_history_value(value)
    if text == "-":
        return text
    token = (field or "").strip().lower()
    if token == "status":
        canonical = _canonical_status_token(text, quiet=True)
        if canonical and canonical in STATUS_LABELS:
            return STATUS_LABELS[canonical]
        return text
    if token in {"task_type", "type"}:
        normalized = _TASK_TYPE_ALIAS.get(text, text)
        label = TASK_TYPE_LABELS.get(normalized)
        return label if label else text
    if token == "archived":
        lowered = text.lower()
        if lowered in {"true", "1", "yes"}:
            return "已归档"
        if lowered in {"false", "0", "no"}:
            return "未归档"
    return text


def _format_history_timestamp(value: Optional[str]) -> str:
    """将历史时间压缩为“月-日 小时:分钟”格式，减少自动换行。"""

    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return _format_local_time(value)
    if SHANGHAI_TZ is not None:
        try:
            dt = dt.astimezone(SHANGHAI_TZ)
        except ValueError:
            return dt.strftime("%m-%d %H:%M")
    return dt.strftime("%m-%d %H:%M")


def _format_history_summary(item: TaskHistoryRecord) -> str:
    """生成首行摘要，突出按钮语义。"""

    event_type = (item.event_type or HISTORY_EVENT_FIELD_CHANGE).strip() or HISTORY_EVENT_FIELD_CHANGE
    payload = _parse_history_payload(item.payload)
    if event_type == HISTORY_EVENT_FIELD_CHANGE:
        field = (item.field or "").strip().lower()
        if field == "create":
            return "创建任务"
        return f"更新{_history_field_label(field)}"
    if event_type == HISTORY_EVENT_TASK_ACTION:
        action = payload.get("action") if isinstance(payload, dict) else None
        if action == "add_note":
            note_type = payload.get("note_type", "misc") if isinstance(payload, dict) else "misc"
            if note_type and note_type != "misc":
                return f"添加备注（{_format_note_type(note_type)}）"
            return "添加备注"
        if action == "push_model":
            return "推送到模型"
        if action == "bug_report":
            return "报告缺陷"
        if action == "summary_request":
            return "生成模型摘要"
        if action == "model_session":
            return "记录模型会话"
        label = action or (item.field or "任务动作")
        return f"执行操作：{label}"
    if event_type == HISTORY_EVENT_MODEL_REPLY:
        return "模型回复"
    if event_type == HISTORY_EVENT_MODEL_SUMMARY:
        return "模型摘要"
    fallback = item.field or event_type
    return _history_field_label(fallback)


def _format_history_description(item: TaskHistoryRecord) -> str:
    event_type = (item.event_type or HISTORY_EVENT_FIELD_CHANGE).strip() or HISTORY_EVENT_FIELD_CHANGE
    payload = _parse_history_payload(item.payload)
    if event_type == HISTORY_EVENT_FIELD_CHANGE:
        field = (item.field or "").strip().lower()
        label = _history_field_label(field)
        if field == "create":
            title_text = _format_history_value("title", item.new_value)
            return f"标题：\"{title_text}\"" if title_text != "-" else "标题：-"
        old_text = _format_history_value(field, item.old_value)
        new_text = _format_history_value(field, item.new_value)
        if old_text == "-" and new_text != "-":
            return f"{label}：{new_text}"
        return f"{label}：{old_text} -> {new_text}"
    if event_type == HISTORY_EVENT_TASK_ACTION:
        action = payload.get("action")
        if action == "add_note":
            note_type = payload.get("note_type", "misc")
            content_text = _trim_history_value(item.new_value)
            lines: list[str] = []
            if note_type and note_type != "misc":
                lines.append(f"类型：{_format_note_type(note_type)}")
            lines.append(f"内容：{content_text}")
            return "\n".join(lines)
        if action == "push_model":
            details: list[str] = []
            supplement_text: Optional[str] = None
            result = payload.get("result") or "success"
            details.append(f"结果：{result}")
            model_name = payload.get("model")
            if model_name:
                details.append(f"模型：{model_name}")
            history_items = payload.get("history_items")
            if isinstance(history_items, int) and history_items > 0:
                details.append(f"包含事件：{history_items}条")
            supplement_raw = payload.get("supplement")
            if supplement_raw is None and payload.get("has_supplement"):
                supplement_raw = item.new_value
            if supplement_raw is not None:
                supplement_text = _trim_history_value(str(supplement_raw))
            detail_text = "；".join(details) if details else "已触发"
            if supplement_text and supplement_text != "-":
                return f"{detail_text}\n补充描述：{supplement_text}"
            if payload.get("has_supplement") and (item.new_value or "").strip():
                supplement_fallback = _trim_history_value(item.new_value)
                if supplement_fallback != "-":
                    return f"{detail_text}\n补充描述：{supplement_fallback}"
            return detail_text
        if action == "bug_report":
            has_logs = bool(payload.get("has_logs"))
            has_repro = bool(payload.get("has_reproduction"))
            note_preview = _trim_history_value(item.new_value)
            details = ["缺陷描述：" + (note_preview or "-")]
            details.append(f"包含复现：{'是' if has_repro else '否'}")
            details.append(f"包含日志：{'是' if has_logs else '否'}")
            return "\n".join(details)
        if action == "summary_request":
            request_id = payload.get("request_id") or (item.new_value or "-")
            model_name = payload.get("model")
            lines = [f"摘要请求 ID：{request_id}"]
            if model_name:
                lines.append(f"目标模型：{model_name}")
            return "\n".join(lines)
        if action == "model_session":
            session = payload.get("session")
            return f"模型会话：{session or '-'}"
        label = action or (item.field or "动作")
        return f"{label}：{_trim_history_value(item.new_value)}"
    if event_type == HISTORY_EVENT_MODEL_REPLY:
        model_name = payload.get("model") or payload.get("source") or ""
        content = payload.get("content") or item.new_value
        text = _trim_history_value(content, limit=HISTORY_MODEL_REPLY_LIMIT)
        prefix = f"{model_name} 回复" if model_name else "模型回复"
        return f"{prefix}：{text}"
    if event_type == HISTORY_EVENT_MODEL_SUMMARY:
        payload_content = payload.get("content") if isinstance(payload, dict) else None
        content = payload_content or item.new_value
        text = _trim_history_value(content, limit=HISTORY_MODEL_SUMMARY_LIMIT)
        return f"摘要内容：{text}"
    fallback_field = item.field or event_type
    return f"{fallback_field}：{_trim_history_value(item.new_value)}"


def _format_history_line(item: TaskHistoryRecord) -> str:
    """以 Markdown 列表形式构建历史文本，首行展示摘要，后续为缩进详情。"""

    timestamp = _format_history_timestamp(item.created_at)
    summary = _format_history_summary(item)
    description = _format_history_description(item)
    detail_lines = [
        line.strip()
        for line in description.splitlines()
        if line.strip()
    ]
    # Markdown 列表使用“- ”起始，后续详情以缩进列表呈现，便于聊天端渲染。
    formatted = [f"- **{summary}** · {timestamp}"]
    for detail in detail_lines:
        formatted.append(f"  - {detail}")
    formatted.append("")  # 追加空行分隔历史记录
    return "\n".join(formatted)


def _format_history_line_for_model(item: TaskHistoryRecord) -> str:
    timestamp = _format_local_time(item.created_at)
    summary = _format_history_summary(item)
    description = _format_history_description(item).replace("\n", " / ")
    if description:
        return f"{timestamp} | {summary} | {description}"
    return f"{timestamp} | {summary}"


def _trim_history_lines_for_limit(lines: list[str], limit: int) -> list[str]:
    if not lines:
        return lines
    joined = "\n".join(lines)
    while len(joined) > limit and lines:
        lines.pop(0)
        joined = "\n".join(lines)
    return lines


async def _build_history_context_for_model(task_id: str) -> tuple[str, int]:
    history = await TASK_SERVICE.list_history(task_id)
    if not history:
        return "", 0
    selected = history[-MODEL_HISTORY_MAX_ITEMS:]
    lines = [_format_history_line_for_model(item) for item in selected]
    trimmed_lines = _trim_history_lines_for_limit(lines, MODEL_HISTORY_MAX_CHARS)
    return "\n".join(trimmed_lines), len(trimmed_lines)


async def _log_task_action(
    task_id: str,
    *,
    action: str,
    actor: Optional[str],
    field: str = "",
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    created_at: Optional[str] = None,
) -> None:
    """封装任务事件写入，出现异常时记录日志避免打断主流程。"""

    data_payload: Optional[Dict[str, Any]]
    if payload is None:
        data_payload = {"action": action}
    else:
        data_payload = {"action": action, **payload}
    try:
        await TASK_SERVICE.log_task_event(
            task_id,
            event_type=HISTORY_EVENT_TASK_ACTION,
            actor=actor,
            field=field,
            old_value=old_value,
            new_value=new_value,
            payload=data_payload,
            created_at=created_at,
        )
    except ValueError as exc:
        worker_log.warning(
            "任务事件写入失败：%s",
            exc,
            extra={"task_id": task_id, **_session_extra()},
        )


async def _auto_push_after_bug_report(task: TaskRecord, *, message: Message, actor: Optional[str]) -> None:
    """缺陷上报完成后尝试自动推送模型，保持与手动推送一致的提示格式。"""

    chat_id = message.chat.id
    if task.status not in MODEL_PUSH_ELIGIBLE_STATUSES:
        await _reply_to_chat(
            chat_id,
            "缺陷已记录，当前状态暂不支持自动推送到模型，如需同步请调整任务状态后手动推送。",
            reply_to=message,
            reply_markup=_build_worker_main_keyboard(),
        )
        return
    try:
        success, prompt, session_path = await _push_task_to_model(
            task,
            chat_id=chat_id,
            reply_to=message,
            supplement=None,
            actor=actor,
        )
    except ValueError as exc:
        worker_log.error(
            "自动推送到模型失败：模板缺失",
            exc_info=exc,
            extra={"task_id": task.id, "status": task.status},
        )
        await _reply_to_chat(
            chat_id,
            "缺陷已记录，但推送模板缺失，请稍后手动重试推送到模型。",
            reply_to=message,
            reply_markup=_build_worker_main_keyboard(),
        )
        return
    if not success:
        await _reply_to_chat(
            chat_id,
            "缺陷已记录，模型当前未就绪，请稍后手动重新推送。",
            reply_to=message,
            reply_markup=_build_worker_main_keyboard(),
        )
        return
    preview_block, preview_parse_mode = _wrap_text_in_code_block(prompt)
    await _reply_to_chat(
        chat_id,
        f"已推送到模型：\n{preview_block}",
        reply_to=message,
        parse_mode=preview_parse_mode,
        reply_markup=_build_worker_main_keyboard(),
    )
    if session_path is not None:
        await _send_session_ack(chat_id, session_path, reply_to=message)


def _build_status_buttons(task_id: str, current_status: str) -> list[list[InlineKeyboardButton]]:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for status in STATUS_DISPLAY_ORDER:
        text = _format_status(status)
        if status == current_status:
            text = f"👉 {text} (当前)"
        row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"task:status:{task_id}:{status}",
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons


def _build_task_actions(task: TaskRecord) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    keyboard.extend(_build_status_buttons(task.id, task.status))
    keyboard.append(
        [
            InlineKeyboardButton(
                text="✏️ 编辑字段",
                callback_data=f"task:edit:{task.id}",
            ),
            InlineKeyboardButton(
                text="🗂️ 归档任务" if not task.archived else "♻️ 恢复任务",
                callback_data=f"task:toggle_archive:{task.id}",
            ),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🚨 报告缺陷",
                callback_data=f"task:bug_report:{task.id}",
            ),
            InlineKeyboardButton(
                text="🕘 查看历史",
                callback_data=f"task:history:{task.id}",
            ),
        ]
    )
    if task.status in MODEL_PUSH_ELIGIBLE_STATUSES:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🚀 推送到模型",
                    callback_data=f"task:push_model:{task.id}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ 返回任务列表",
                callback_data=TASK_DETAIL_BACK_CALLBACK,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _build_task_desc_confirm_keyboard() -> ReplyKeyboardMarkup:
    """任务描述确认阶段的菜单按钮。"""

    rows = [
        [KeyboardButton(text=TASK_DESC_CONFIRM_TEXT)],
        [KeyboardButton(text=TASK_DESC_RETRY_TEXT), KeyboardButton(text=TASK_DESC_CANCEL_TEXT)],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_task_desc_input_keyboard() -> ReplyKeyboardMarkup:
    """任务描述输入阶段的菜单按钮。"""

    rows = [
        [KeyboardButton(text=TASK_DESC_CLEAR_TEXT), KeyboardButton(text=TASK_DESC_REPROMPT_TEXT)],
        [KeyboardButton(text=TASK_DESC_CANCEL_TEXT)],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=False)


def _build_task_desc_cancel_keyboard() -> ReplyKeyboardMarkup:
    """仅保留取消操作的菜单，用于提示场景。"""

    rows = [[KeyboardButton(text=TASK_DESC_CANCEL_TEXT)]]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_task_desc_confirm_text(preview_segment: str) -> str:
    """生成任务描述确认阶段的提示文案。"""

    return (
        "请确认新的任务描述：\n"
        f"{preview_segment}\n\n"
        "1. 点击“✅ 确认更新”立即保存\n"
        "2. 点击“✏️ 重新输入”重新填写描述\n"
        "3. 点击“❌ 取消”终止本次编辑"
    )


async def _prompt_task_description_input(
    target: Optional[Message],
    *,
    current_description: str,
) -> None:
    """向用户展示当前描述，提供取消按钮及后续操作提示。"""

    if target is None:
        # Telegram 已删除原消息时直接忽略，避免流程中断。
        return
    preview = (current_description or "").strip()
    preview_segment = preview or "（当前描述为空，确认后将保存为空）"
    await target.answer(
        "当前描述如下，可复制后直接编辑，菜单中的选项可快速完成清空或取消操作。",
        reply_markup=_build_task_desc_input_keyboard(),
    )
    preview_block, preview_parse_mode = _wrap_text_in_code_block(preview_segment)
    try:
        await target.answer(
            preview_block,
            parse_mode=preview_parse_mode,
        )
    except TelegramBadRequest:
        await target.answer(preview_segment)
    await target.answer(
        "请直接发送新的任务描述，或通过菜单按钮执行快捷操作。",
    )


async def _begin_task_desc_edit_flow(
    *,
    state: FSMContext,
    task: TaskRecord,
    actor: str,
    origin_message: Optional[Message],
) -> None:
    """统一初始化任务描述编辑 FSM，兼容回调与命令入口。"""

    if origin_message is None:
        return
    await state.clear()
    await state.update_data(
        task_id=task.id,
        actor=actor,
        current_description=task.description or "",
    )
    await state.set_state(TaskDescriptionStates.waiting_content)
    await _prompt_task_description_input(
        origin_message,
        current_description=task.description or "",
    )


def _extract_command_args(text: Optional[str]) -> str:
    if not text:
        return ""
    stripped = text.strip()
    if not stripped:
        return ""
    if " " not in stripped:
        return ""
    return stripped.split(" ", 1)[1].strip()


async def _answer_with_markdown(
    message: Message,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
) -> Optional[Message]:
    prepared = _prepare_model_payload(text)
    try:
        sent = await message.answer(
            prepared,
            parse_mode=_parse_mode_value(),
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        worker_log.warning(
            "发送消息失败：%s",
            exc,
            extra={"chat": getattr(message.chat, "id", None)},
        )
        return None
    return sent


async def _edit_message_with_markdown(
    callback: CallbackQuery,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    prepared = _prepare_model_payload(text)
    await callback.message.edit_text(
        prepared,
        parse_mode=_parse_mode_value(),
        reply_markup=reply_markup,
    )


async def _try_edit_message(
    message: Optional[Message],
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    if message is None:
        return False
    prepared = _prepare_model_payload(text)
    try:
        await message.edit_text(
            prepared,
            parse_mode=_parse_mode_value(),
            reply_markup=reply_markup,
        )
        return True
    except TelegramBadRequest as exc:
        worker_log.info(
            "编辑任务列表消息失败，将改用新消息展示",
            extra={"reason": _extract_bad_request_message(exc)},
        )
    return False


def _build_priority_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=str(i)) for i in range(1, 6)],
        [KeyboardButton(text=SKIP_TEXT)],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_task_type_keyboard() -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    current_row: list[KeyboardButton] = []
    for task_type in TASK_TYPES:
        current_row.append(KeyboardButton(text=_format_task_type(task_type)))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([KeyboardButton(text="取消")])
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_description_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SKIP_TEXT)],
        [KeyboardButton(text="取消")],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_confirm_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="✅ 确认创建")],
        [KeyboardButton(text="❌ 取消")],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _build_bug_confirm_keyboard() -> ReplyKeyboardMarkup:
    """缺陷提交流程确认键盘。"""

    rows = [
        [KeyboardButton(text="✅ 确认提交")],
        [KeyboardButton(text="❌ 取消")],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _collect_message_payload(message: Message) -> str:
    """提取消息中的文字与附件信息，方便写入缺陷记录。"""

    parts: list[str] = []
    text = _normalize_choice_token(message.text or message.caption)
    if text:
        parts.append(text)
    if message.photo:
        file_id = message.photo[-1].file_id
        parts.append(f"[图片:{file_id}]")
    if message.document:
        doc = message.document
        name = doc.file_name or doc.file_id
        parts.append(f"[文件:{name}]")
    if message.voice:
        parts.append(f"[语音:{message.voice.file_id}]")
    if message.video:
        parts.append(f"[视频:{message.video.file_id}]")
    return "\n".join(parts).strip()


def _summarize_note_text(value: str) -> str:
    """压缩备注内容，维持主要信息并控制长度。"""

    cleaned = normalize_newlines(value or "").strip()
    return cleaned.replace("\n", " / ")


def _build_bug_report_intro(task: TaskRecord) -> str:
    """生成缺陷报告开场提示。"""

    # 直接拼接命令文本，确保提示语中不出现 Markdown 转义后的反斜杠。
    task_code = f"/{task.id}" if task.id else "-"
    title = task.title or "-"
    return (
        f"正在为任务 {task_code}（{title}）记录缺陷。\n"
        "请先描述缺陷现象（必填），例如发生了什么、期待的行为是什么。"
    )


def _build_bug_repro_prompt() -> str:
    """生成复现步骤提示。"""

    return (
        "若有复现步骤，请按顺序列出，例如：\n"
        "1. 打开页面...\n"
        "2. 操作...\n"
        "如暂无可发送“跳过”，发送“取消”随时结束流程。"
    )


def _build_bug_log_prompt() -> str:
    """生成日志信息提示。"""

    return (
        "请提供错误日志、截图或相关附件。\n"
        "若无额外信息，可发送“跳过”，发送“取消”结束流程。"
    )


def _build_bug_preview_text(
    *,
    task: TaskRecord,
    description: str,
    reproduction: str,
    logs: str,
    reporter: str,
) -> str:
    """构建缺陷预览文本，便于用户确认。"""

    # 预览信息面向纯文本消息，直接使用任务命令避免额外的反斜杠。
    task_code = f"/{task.id}" if task.id else "-"
    parts = [
        f"任务编码：{task_code}",
        f"缺陷描述：{description or '-'}",
        f"复现步骤：{reproduction or '-'}",
        f"日志信息：{logs or '-'}",
        f"报告人：{reporter}",
    ]
    return "\n".join(parts)


def _build_summary_prompt(
    task: TaskRecord,
    *,
    request_id: str,
    history_text: str,
    notes: Sequence[TaskNoteRecord],
) -> str:
    """构造模型摘要提示词，要求携带请求标识。"""

    # 摘要提示词是发送给模型的，使用纯文本格式，不需要 Markdown 转义
    task_code = f"/{task.id}" if task.id else "-"
    title = task.title or "-"
    status_label = STATUS_LABELS.get(task.status, task.status)
    note_lines: list[str] = []
    if notes:
        note_lines.append("备注汇总：")
        for note in notes[-5:]:
            label = NOTE_LABELS.get(note.note_type or "", note.note_type or "备注")
            content = _summarize_note_text(note.content or "")
            timestamp = _format_local_time(note.created_at)
            note_lines.append(f"- [{label}] {timestamp} — {content or '-'}")
    else:
        note_lines.append("备注汇总：-")
    history_lines = ["历史记录："]
    if history_text.strip():
        history_lines.extend(history_text.splitlines())
    else:
        history_lines.append("-")
    instructions = [
        "进入摘要阶段...",
        f"任务编码：{task_code}",
        f"SUMMARY_REQUEST_ID::{request_id}，模型必须原样回传。",
        "",
        f"任务标题：{title}",
        f"任务阶段：{status_label}",
        f"优先级：{task.priority}",
        "",
        f"请基于以下信息为任务 {task_code} 生成处理摘要。",
        "输出要求：",
        "- 第一行必须原样包含 SUMMARY_REQUEST_ID::{request_id}。",
        "- 汇总任务目标、近期动作、当前状态与待办事项。",
        "- 采用项目同事可直接阅读的简洁段落或列表格式。",
        "- 若存在未解决缺陷或测试问题请明确指出。",
        "",
    ]
    instructions.extend(note_lines)
    instructions.append("")
    instructions.extend(history_lines)
    instructions.append("")
    instructions.append("请在输出末尾补充下一步建议。")
    return "\n".join(instructions)


def _build_push_supplement_prompt() -> str:
    return (
        "请输入补充任务描述，建议说明任务背景与期望结果。\n"
        "若暂时没有可点击“跳过”按钮或直接发送空消息，发送“取消”可终止。"
    )


async def _prompt_model_supplement_input(message: Message) -> None:
    await message.answer(
        _build_push_supplement_prompt(),
        reply_markup=_build_description_keyboard(),
    )


def _build_task_search_prompt() -> str:
    return (
        "请输入任务搜索关键词（至少 2 个字符），支持标题和描述模糊匹配。\n"
        "发送“跳过”或“取消”可返回任务列表。"
    )


async def _prompt_task_search_keyword(message: Message) -> None:
    await message.answer(
        _build_task_search_prompt(),
        reply_markup=_build_description_keyboard(),
    )


def _build_edit_field_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="标题"), KeyboardButton(text="优先级")],
        [KeyboardButton(text="类型"), KeyboardButton(text="描述")],
        [KeyboardButton(text="状态")],
        [KeyboardButton(text="取消")],
    ]
    _number_reply_buttons(rows)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


async def _load_task_context(
    task_id: str,
    *,
    include_history: bool = False,
) -> tuple[TaskRecord, Sequence[TaskNoteRecord], Sequence[TaskHistoryRecord]]:
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        raise ValueError("任务不存在")
    notes = await TASK_SERVICE.list_notes(task_id)
    history: Sequence[TaskHistoryRecord]
    if include_history:
        history = await TASK_SERVICE.list_history(task_id)
    else:
        history = ()
    return task, notes, history


async def _render_task_detail(task_id: str) -> tuple[str, InlineKeyboardMarkup]:
    task, notes, _ = await _load_task_context(task_id)
    detail_text = _format_task_detail(task, notes=notes)
    return detail_text, _build_task_actions(task)


@dataclass(slots=True)
class _HistoryViewPage:
    """历史分页渲染所需的文本切片。"""

    lines: list[str]
    notice: str
    truncated: bool


def _build_truncated_history_entry(item: TaskHistoryRecord) -> str:
    """生成单条历史的截断提示文本，保留摘要时间信息。"""

    timestamp = _format_history_timestamp(item.created_at)
    summary = _format_history_summary(item)
    return "\n".join(
        [
            f"- **{summary}** · {timestamp}",
            "  - ⚠️ 该记录内容较长，仅展示摘要概要。",
        ]
    )


def _select_truncation_variant(
    entry_text: str,
    *,
    notice: str,
    body_limit: int,
) -> tuple[str, str]:
    """在长度限制内挑选截断文本与提示。"""

    variants = [
        (entry_text, notice),
        ("- ⚠️ 历史记录内容过长，已简化展示。", notice),
        ("- ⚠️ 历史记录内容过长，已简化展示。", HISTORY_TRUNCATION_NOTICE_SHORT),
        ("- ⚠️ 已截断", HISTORY_TRUNCATION_NOTICE_SHORT),
    ]
    for candidate_text, candidate_notice in variants:
        combined = "\n\n".join([candidate_text, candidate_notice])
        if len(_prepare_model_payload(combined)) <= body_limit:
            return candidate_text, candidate_notice
    # 最差情况下仅返回极短提示，避免再次触发超长错误。
    fallback_text = "- ⚠️ 历史记录已截断，详细内容请导出查看。"
    return fallback_text, HISTORY_TRUNCATION_NOTICE_SHORT


def _build_task_history_view(
    task: TaskRecord,
    history: Sequence[TaskHistoryRecord],
    *,
    page: int,
) -> tuple[str, InlineKeyboardMarkup, int, int]:
    """根据任务历史构造分页视图内容与内联按钮。"""

    limited = list(history[-MODEL_HISTORY_MAX_ITEMS:])
    total_items = len(limited)
    if total_items == 0:
        raise ValueError("暂无事件记录")

    # 历史记录会被包裹在代码块中显示，使用纯文本格式，不需要 Markdown 转义
    title_text = normalize_newlines(task.title or "").strip() or "-"
    title_display = title_text

    digit_width = len(str(max(total_items, 1)))
    placeholder_page = "9" * digit_width
    header_placeholder = "\n".join(
        [
            f"任务 {task.id} 事件历史（最近 {total_items} 条）",
            f"标题：{title_display}",
            f"页码：{placeholder_page} / {placeholder_page}",
        ]
    )
    header_reserved = len(_prepare_model_payload(header_placeholder))
    # 保留额外两个换行为正文与抬头的分隔，确保总长度不超 4096。
    body_limit = max(1, TELEGRAM_MESSAGE_LIMIT - header_reserved - 2)

    page_size = max(1, TASK_HISTORY_PAGE_SIZE)
    formatted_entries = [_format_history_line(item).rstrip("\n") for item in limited]
    pages: list[_HistoryViewPage] = []
    index = 0
    while index < total_items:
        current_lines: list[str] = []
        truncated = False
        notice_text = ""
        while index < total_items and len(current_lines) < page_size:
            candidate_lines = [*current_lines, formatted_entries[index]]
            candidate_body = "\n\n".join(candidate_lines)
            if len(_prepare_model_payload(candidate_body)) <= body_limit:
                current_lines = candidate_lines
                index += 1
                continue
            break
        if not current_lines:
            # 单条记录即超出限制，需降级展示并追加截断提示。
            entry = limited[index]
            entry_text = _build_truncated_history_entry(entry)
            truncated_text, notice_text = _select_truncation_variant(
                entry_text,
                notice=HISTORY_TRUNCATION_NOTICE,
                body_limit=body_limit,
            )
            current_lines = [truncated_text]
            truncated = True
            index += 1
        pages.append(_HistoryViewPage(lines=current_lines, notice=notice_text, truncated=truncated))

    total_pages = len(pages)
    normalized_page = page if 1 <= page <= total_pages else total_pages
    selected = pages[normalized_page - 1]
    body_segments = list(selected.lines)
    notice_text = selected.notice
    if selected.truncated and not notice_text:
        # 未能放入默认提示时至少保留简短信息。
        notice_text = HISTORY_TRUNCATION_NOTICE_SHORT
    if notice_text:
        body_segments.append(notice_text)
    body_text = "\n\n".join(body_segments).strip()

    header_text = "\n".join(
        [
            f"任务 {task.id} 事件历史（最近 {total_items} 条）",
            f"标题：{title_display}",
            f"页码：{normalized_page} / {total_pages}",
        ]
    )
    text = f"{header_text}\n\n{body_text}" if body_text else header_text
    prepared = _prepare_model_payload(text)
    if len(prepared) > TELEGRAM_MESSAGE_LIMIT:
        worker_log.warning(
            "历史视图仍超过 Telegram 限制，使用安全提示内容",
            extra={"task_id": task.id, "page": str(normalized_page), "length": str(len(prepared))},
        )
        text = "\n".join(
            [
                f"任务 {task.id} 事件历史（最近 {total_items} 条）",
                f"标题：{title_display}",
                f"页码：{normalized_page} / {total_pages}",
                "",
                "⚠️ 历史记录内容超出 Telegram 长度限制，请导出或筛选后重试。",
            ]
        )

    nav_row: list[InlineKeyboardButton] = []
    if normalized_page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"{TASK_HISTORY_PAGE_CALLBACK}:{task.id}:{normalized_page - 1}",
            )
        )
    if normalized_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"{TASK_HISTORY_PAGE_CALLBACK}:{task.id}:{normalized_page + 1}",
            )
        )

    keyboard_rows: list[list[InlineKeyboardButton]] = []
    if nav_row:
        keyboard_rows.append(nav_row)
    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ 返回任务详情",
                callback_data=f"{TASK_HISTORY_BACK_CALLBACK}:{task.id}",
            )
        ]
    )

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard_rows), normalized_page, total_pages


async def _render_task_history(
    task_id: str,
    page: int,
) -> tuple[str, InlineKeyboardMarkup, int, int]:
    """渲染指定任务的历史视图，返回内容、按钮及页码信息。"""

    task, _notes, history_records = await _load_task_context(task_id, include_history=True)
    trimmed = list(history_records[-MODEL_HISTORY_MAX_ITEMS:])
    if not trimmed:
        raise ValueError("暂无事件记录")
    return _build_task_history_view(task, trimmed, page=page)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


ANSI_ESCAPE_RE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


NOISE_PATTERNS = (
    "Working(",
    "Deciding whether to run command",
    "⌃J newline",
    "⌃T transcript",
    "⌃C quit",
    "tokens used",
    "Press Enter to confirm",
    "Select Approval Mode",
    "Find and fix a bug in @filename",
    "Write tests for @filename",
)


def postprocess_tmux_output(raw: str) -> str:
    text = normalize_newlines(raw)
    text = text.replace("\x08", "")
    text = strip_ansi(text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in {"%", '"'}:
            continue
        if any(pattern in stripped for pattern in NOISE_PATTERNS):
            continue
        if stripped.startswith("▌"):
            stripped = stripped.lstrip("▌ ")
            if not stripped:
                continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def _session_id_from_path(path: Optional[Path]) -> str:
    """将会话路径转换为日志使用的标识。"""
    if path is None:
        return "-"
    stem = path.stem
    return stem or path.name or "-"


def _session_extra(*, path: Optional[Path] = None, key: Optional[str] = None) -> Dict[str, str]:
    if key and path is None:
        try:
            path = Path(key)
        except Exception:
            return {"session": key or "-"}
    return {"session": _session_id_from_path(path)}


def _initialize_known_rollouts() -> None:
    if CODEX_SESSION_FILE_PATH:
        KNOWN_ROLLOUTS.add(str(resolve_path(CODEX_SESSION_FILE_PATH)))


def tmux_capture_since(log_path: Path | str, start_pos: int, idle: float = 2.0, timeout: float = 120.0) -> str:
    # 从日志文件偏移量开始读取，直到连续 idle 秒无新增或超时
    start = time.time()
    p = resolve_path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # 等待日志文件出现
    for _ in range(50):
        if p.exists(): break
        time.sleep(0.1)
    buf = []
    last = time.time()
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(start_pos)
        while True:
            chunk = f.read()
            if chunk:
                buf.append(chunk)
                last = time.time()
            else:
                time.sleep(0.2)
            if time.time() - last >= idle:
                break
            if time.time() - start > timeout:
                break
    return "".join(buf)


SESSION_OFFSETS: Dict[str, int] = {}
CHAT_SESSION_MAP: Dict[int, str] = {}
CHAT_WATCHERS: Dict[int, asyncio.Task] = {}
CHAT_LAST_MESSAGE: Dict[int, Dict[str, str]] = {}
CHAT_FAILURE_NOTICES: Dict[int, float] = {}
CHAT_PLAN_MESSAGES: Dict[int, int] = {}
CHAT_PLAN_TEXT: Dict[int, str] = {}
CHAT_PLAN_COMPLETION: Dict[int, bool] = {}
CHAT_DELIVERED_HASHES: Dict[int, Dict[str, set[str]]] = {}
CHAT_DELIVERED_OFFSETS: Dict[int, Dict[str, set[int]]] = {}
CHAT_REPLY_COUNT: Dict[int, Dict[str, int]] = {}
CHAT_COMPACT_STATE: Dict[int, Dict[str, Dict[str, Any]]] = {}
# 长轮询状态：用于延迟轮询机制
CHAT_LONG_POLL_STATE: Dict[int, Dict[str, Any]] = {}
CHAT_LONG_POLL_LOCK: Optional[asyncio.Lock] = None  # 在事件循环启动后初始化
SUMMARY_REQUEST_TIMEOUT_SECONDS = 300.0


@dataclass(slots=True)
class PendingSummary:
    """记录待落库的模型摘要请求。"""

    task_id: str
    request_id: str
    actor: Optional[str]
    session_key: str
    session_path: Path
    created_at: float
    buffer: str = ""


PENDING_SUMMARIES: Dict[str, PendingSummary] = {}

# --- 任务视图上下文缓存 ---
TaskViewKind = Literal["list", "search", "detail", "history"]


@dataclass
class TaskViewState:
    """缓存任务视图的渲染参数，支持消息编辑式导航。"""

    kind: TaskViewKind
    data: Dict[str, Any]


TASK_VIEW_STACK: Dict[int, Dict[int, List[TaskViewState]]] = {}


def _task_view_stack(chat_id: int) -> Dict[int, List[TaskViewState]]:
    """获取指定聊天的视图栈映射。"""

    return TASK_VIEW_STACK.setdefault(chat_id, {})


def _push_task_view(chat_id: int, message_id: int, state: TaskViewState) -> None:
    """压入新的视图状态，用于进入详情等场景。"""

    stack = _task_view_stack(chat_id).setdefault(message_id, [])
    stack.append(state)


def _replace_task_view(chat_id: int, message_id: int, state: TaskViewState) -> None:
    """替换栈顶视图，常见于列表分页或刷新操作。"""

    stack = _task_view_stack(chat_id).setdefault(message_id, [])
    if stack:
        stack[-1] = state
    else:
        stack.append(state)


def _peek_task_view(chat_id: int, message_id: int) -> Optional[TaskViewState]:
    """查看当前栈顶视图。"""

    stack = TASK_VIEW_STACK.get(chat_id, {}).get(message_id)
    if not stack:
        return None
    return stack[-1]


def _pop_task_view(chat_id: int, message_id: int) -> Optional[TaskViewState]:
    """弹出栈顶视图，必要时清理空栈。"""

    chat_views = TASK_VIEW_STACK.get(chat_id)
    if not chat_views:
        return None
    stack = chat_views.get(message_id)
    if not stack:
        return None
    state = stack.pop()
    if not stack:
        chat_views.pop(message_id, None)
    if not chat_views:
        TASK_VIEW_STACK.pop(chat_id, None)
    return state


def _clear_task_view(chat_id: int, message_id: Optional[int] = None) -> None:
    """清理缓存，防止内存泄漏或上下文污染。"""

    if message_id is None:
        TASK_VIEW_STACK.pop(chat_id, None)
        return
    chat_views = TASK_VIEW_STACK.get(chat_id)
    if not chat_views:
        return
    chat_views.pop(message_id, None)
    if not chat_views:
        TASK_VIEW_STACK.pop(chat_id, None)


def _init_task_view_context(message: Optional[Message], state: TaskViewState) -> None:
    """初始化指定消息的视图栈（新发送的列表或搜索视图）。"""

    if message is None:
        return
    chat = getattr(message, "chat", None)
    if chat is None:
        return
    chat_id = chat.id
    message_id = message.message_id
    _clear_task_view(chat_id, message_id)
    _push_task_view(chat_id, message_id, state)


def _set_task_view_context(message: Optional[Message], state: TaskViewState) -> None:
    """更新现有消息的栈顶视图，保持已有历史。"""

    if message is None:
        return
    chat = getattr(message, "chat", None)
    if chat is None:
        return
    _replace_task_view(chat.id, message.message_id, state)


def _push_detail_view(message: Optional[Message], task_id: str) -> None:
    """在视图栈中压入详情视图，便于回退。"""

    if message is None:
        return
    chat = getattr(message, "chat", None)
    if chat is None:
        return
    _push_task_view(
        chat.id,
        message.message_id,
        TaskViewState(kind="detail", data={"task_id": task_id}),
    )


def _pop_detail_view(message: Optional[Message]) -> Optional[TaskViewState]:
    """弹出详情视图，返回移除的状态。"""

    if message is None:
        return None
    chat = getattr(message, "chat", None)
    if chat is None:
        return None
    state = _pop_task_view(chat.id, message.message_id)
    if state and state.kind != "detail":
        # 栈顶不是详情，说明上下文异常，放回以免破坏结构。
        _push_task_view(chat.id, message.message_id, state)
        return None
    return state


async def _render_task_view_from_state(state: TaskViewState) -> tuple[str, InlineKeyboardMarkup]:
    """根据视图状态重新渲染对应的任务界面。"""

    if state.kind == "list":
        status = state.data.get("status")
        page = int(state.data.get("page", 1) or 1)
        limit = int(state.data.get("limit", DEFAULT_PAGE_SIZE) or DEFAULT_PAGE_SIZE)
        return await _build_task_list_view(status=status, page=page, limit=limit)
    if state.kind == "search":
        keyword = state.data.get("keyword", "")
        page = int(state.data.get("page", 1) or 1)
        limit = int(state.data.get("limit", DEFAULT_PAGE_SIZE) or DEFAULT_PAGE_SIZE)
        origin_status = state.data.get("origin_status")
        origin_page = int(state.data.get("origin_page", 1) or 1)
        return await _build_task_search_view(
            keyword,
            page=page,
            limit=limit,
            origin_status=origin_status,
            origin_page=origin_page,
        )
    if state.kind == "detail":
        task_id = state.data.get("task_id")
        if not task_id:
            raise ValueError("任务详情缺少 task_id")
        return await _render_task_detail(task_id)
    if state.kind == "history":
        task_id = state.data.get("task_id")
        if not task_id:
            raise ValueError("任务历史缺少 task_id")
        page = int(state.data.get("page", 1) or 1)
        text, markup, _, _ = await _render_task_history(task_id, page)
        return text, markup
    raise ValueError(f"未知的任务视图类型：{state.kind}")


def _make_list_view_state(*, status: Optional[str], page: int, limit: int) -> TaskViewState:
    """构造列表视图的上下文。"""

    return TaskViewState(
        kind="list",
        data={
            "status": status,
            "page": page,
            "limit": limit,
        },
    )


def _make_search_view_state(
    *,
    keyword: str,
    page: int,
    limit: int,
    origin_status: Optional[str],
    origin_page: int,
) -> TaskViewState:
    """构造搜索视图的上下文。"""

    return TaskViewState(
        kind="search",
        data={
            "keyword": keyword,
            "page": page,
            "limit": limit,
            "origin_status": origin_status,
            "origin_page": origin_page,
        },
    )


def _make_history_view_state(*, task_id: str, page: int) -> TaskViewState:
    """构造历史视图的上下文。"""

    return TaskViewState(
        kind="history",
        data={
            "task_id": task_id,
            "page": page,
        },
    )

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-9;?]*[ -/]*[@-~]")


def _get_last_message(chat_id: int, session_key: str) -> Optional[str]:
    sessions = CHAT_LAST_MESSAGE.get(chat_id)
    if not sessions:
        return None
    return sessions.get(session_key)


def _set_last_message(chat_id: int, session_key: str, text: str) -> None:
    CHAT_LAST_MESSAGE.setdefault(chat_id, {})[session_key] = text


def _clear_last_message(chat_id: int, session_key: Optional[str] = None) -> None:
    if session_key is None:
        CHAT_LAST_MESSAGE.pop(chat_id, None)
        return
    sessions = CHAT_LAST_MESSAGE.get(chat_id)
    if not sessions:
        return
    sessions.pop(session_key, None)
    if not sessions:
        CHAT_LAST_MESSAGE.pop(chat_id, None)


def _reset_delivered_hashes(chat_id: int, session_key: Optional[str] = None) -> None:
    if session_key is None:
        removed = CHAT_DELIVERED_HASHES.pop(chat_id, None)
        if removed:
            worker_log.info(
                "清空聊天的已发送消息哈希",
                extra={"chat": chat_id},
            )
        return
    sessions = CHAT_DELIVERED_HASHES.get(chat_id)
    if not sessions:
        return
    if session_key in sessions:
        sessions.pop(session_key, None)
        worker_log.info(
            "清空会话的已发送消息哈希",
            extra={
                "chat": chat_id,
                **_session_extra(key=session_key),
            },
        )
    if not sessions:
        CHAT_DELIVERED_HASHES.pop(chat_id, None)


def _get_delivered_hashes(chat_id: int, session_key: str) -> set[str]:
    return CHAT_DELIVERED_HASHES.setdefault(chat_id, {}).setdefault(session_key, set())


def _reset_compact_tracking(chat_id: int, session_key: Optional[str] = None) -> None:
    """清理自动压缩相关状态，避免历史计数影响后续判断。"""

    if session_key is None:
        CHAT_REPLY_COUNT.pop(chat_id, None)
        CHAT_COMPACT_STATE.pop(chat_id, None)
        return

    reply_sessions = CHAT_REPLY_COUNT.get(chat_id)
    if reply_sessions is not None:
        reply_sessions.pop(session_key, None)
        if not reply_sessions:
            CHAT_REPLY_COUNT.pop(chat_id, None)

    compact_sessions = CHAT_COMPACT_STATE.get(chat_id)
    if compact_sessions is not None:
        compact_sessions.pop(session_key, None)
        if not compact_sessions:
            CHAT_COMPACT_STATE.pop(chat_id, None)


def _increment_reply_count(chat_id: int, session_key: str) -> int:
    sessions = CHAT_REPLY_COUNT.setdefault(chat_id, {})
    sessions[session_key] = sessions.get(session_key, 0) + 1
    return sessions[session_key]


def _cleanup_expired_summaries() -> None:
    """移除超时未完成的摘要请求。"""

    if not PENDING_SUMMARIES:
        return
    now = time.monotonic()
    expired = [
        key
        for key, pending in PENDING_SUMMARIES.items()
        if now - pending.created_at > SUMMARY_REQUEST_TIMEOUT_SECONDS
    ]
    for key in expired:
        PENDING_SUMMARIES.pop(key, None)
        worker_log.info(
            "摘要请求超时已清理",
            extra={"session": key},
        )


def _extract_task_ids_from_text(text: str) -> list[str]:
    """从模型文本中提取标准任务编号。"""

    if not text:
        return []
    matches = TASK_REFERENCE_PATTERN.findall(text)
    normalized: list[str] = []
    for token in matches:
        normalized_id = _normalize_task_id(token)
        if normalized_id and normalized_id not in normalized:
            normalized.append(normalized_id)
    return normalized


async def _log_model_reply_event(
    task_id: str,
    *,
    content: str,
    session_path: Path,
    event_offset: int,
) -> None:
    """将模型回复写入任务历史。"""

    trimmed = _trim_history_value(content, limit=HISTORY_DISPLAY_VALUE_LIMIT)
    payload = {
        "model": ACTIVE_MODEL or "",
        "session": str(session_path),
        "offset": event_offset,
    }
    if content:
        payload["content"] = content[:MODEL_REPLY_PAYLOAD_LIMIT]
    try:
        await TASK_SERVICE.log_task_event(
            task_id,
            event_type=HISTORY_EVENT_MODEL_REPLY,
            actor=f"model/{ACTIVE_MODEL or 'codex'}",
            new_value=trimmed,
            payload=payload,
        )
    except ValueError:
        worker_log.warning(
            "模型回复写入失败：任务不存在",
            extra={"task_id": task_id, **_session_extra(path=session_path)},
        )


async def _maybe_finalize_summary(
    session_key: str,
    *,
    content: str,
    event_offset: int,
    session_path: Path,
) -> None:
    """检测并记录模型返回的摘要。"""

    pending = PENDING_SUMMARIES.get(session_key)
    if not pending:
        return
    request_tag = f"SUMMARY_REQUEST_ID::{pending.request_id}"
    normalized_buffer = (pending.buffer or "").replace("\\_", "_")
    normalized_content = content.replace("\\_", "_")
    combined_text = (
        f"{normalized_buffer}\n{normalized_content}"
        if normalized_buffer
        else normalized_content
    )
    if request_tag not in combined_text:
        pending.buffer = combined_text
        return
    summary_text = combined_text
    trimmed = _trim_history_value(summary_text, limit=HISTORY_DISPLAY_VALUE_LIMIT)
    payload = {
        "request_id": pending.request_id,
        "model": ACTIVE_MODEL or "",
        "session": str(session_path),
        "offset": event_offset,
    }
    if summary_text:
        payload["content"] = summary_text[:MODEL_SUMMARY_PAYLOAD_LIMIT]
    try:
        await TASK_SERVICE.log_task_event(
            pending.task_id,
            event_type="model_summary",
            actor=pending.actor,
            new_value=trimmed,
            payload=payload,
        )
    except ValueError:
        worker_log.warning(
            "摘要写入失败：任务不存在",
            extra={"task_id": pending.task_id, **_session_extra(path=session_path)},
        )
    finally:
        PENDING_SUMMARIES.pop(session_key, None)


async def _handle_model_response(
    *,
    chat_id: int,
    session_key: str,
    session_path: Path,
    event_offset: int,
    content: str,
) -> None:
    """统一持久化模型输出，并处理摘要落库。"""

    _cleanup_expired_summaries()
    await _maybe_finalize_summary(
        session_key,
        content=content,
        event_offset=event_offset,
        session_path=session_path,
    )
    # 仅在摘要请求落库时记录历史，普通模型回复不再写入 task_history。
    return


def _set_reply_count(chat_id: int, session_key: str, value: int) -> None:
    sessions = CHAT_REPLY_COUNT.setdefault(chat_id, {})
    sessions[session_key] = max(value, 0)


def _get_compact_state(chat_id: int, session_key: str) -> Dict[str, Any]:
    sessions = CHAT_COMPACT_STATE.setdefault(chat_id, {})
    state = sessions.get(session_key)
    if state is None:
        state = {"pending": False, "triggered_at": 0.0}
        sessions[session_key] = state
    return state


def _is_compact_pending(chat_id: int, session_key: str) -> bool:
    return bool(_get_compact_state(chat_id, session_key).get("pending"))


def _mark_compact_pending(chat_id: int, session_key: str) -> None:
    state = _get_compact_state(chat_id, session_key)
    state["pending"] = True
    state["triggered_at"] = time.monotonic()


def _clear_compact_pending(chat_id: int, session_key: str) -> float:
    state = _get_compact_state(chat_id, session_key)
    started = float(state.get("triggered_at") or 0.0)
    state["pending"] = False
    state["triggered_at"] = 0.0
    return started


async def _send_plain_notice(chat_id: int, text: str) -> None:
    """向用户发送无需 Markdown 格式的提示信息。"""

    bot = current_bot()

    async def _do() -> None:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=None)

    await _send_with_retry(_do)


async def _maybe_trigger_auto_compact(chat_id: int, session_key: str, count: int) -> None:
    """达到阈值后自动执行 /compact，同时向用户提示。"""

    if AUTO_COMPACT_THRESHOLD <= 0:
        return
    if count < AUTO_COMPACT_THRESHOLD:
        return
    if _is_compact_pending(chat_id, session_key):
        return

    notice = (
        f"模型已连续回复 {count} 条，准备自动执行 /compact，请稍候。"
    )
    await _send_plain_notice(chat_id, notice)

    try:
        tmux_send_line(TMUX_SESSION, "/compact")
    except subprocess.CalledProcessError as exc:
        worker_log.error(
            "自动触发 /compact 失败: %s",
            exc,
            extra={
                "chat": chat_id,
                **_session_extra(key=session_key),
            },
        )
        failure_text = f"自动执行 /compact 失败：{exc}"
        await _send_plain_notice(chat_id, failure_text)
        fallback = max(AUTO_COMPACT_THRESHOLD - 1, 0)
        _set_reply_count(chat_id, session_key, fallback)
        return

    _set_reply_count(chat_id, session_key, 0)
    _mark_compact_pending(chat_id, session_key)

    worker_log.info(
        "已自动发送 /compact",
        extra={
            "chat": chat_id,
            **_session_extra(key=session_key),
            "threshold": str(AUTO_COMPACT_THRESHOLD),
        },
    )

    await _send_plain_notice(chat_id, "已向模型发送 /compact，等待整理结果。")


async def _post_delivery_compact_checks(chat_id: int, session_key: str) -> None:
    """在模型消息发送成功后执行计数和自动压缩检查。"""

    if _is_compact_pending(chat_id, session_key):
        started = _clear_compact_pending(chat_id, session_key)
        elapsed = 0.0
        if started > 0:
            elapsed = max(time.monotonic() - started, 0.0)
        duration_hint = f"，耗时约 {elapsed:.1f} 秒" if elapsed > 0 else ""
        await _send_plain_notice(
            chat_id,
            f"自动执行 /compact 已完成{duration_hint}。",
        )
        _set_reply_count(chat_id, session_key, 0)

    if AUTO_COMPACT_THRESHOLD <= 0:
        return

    new_count = _increment_reply_count(chat_id, session_key)
    await _maybe_trigger_auto_compact(chat_id, session_key, new_count)

def _reset_delivered_offsets(chat_id: int, session_key: Optional[str] = None) -> None:
    if session_key is None:
        removed = CHAT_DELIVERED_OFFSETS.pop(chat_id, None)
        if removed:
            worker_log.info(
                "清空聊天的已处理事件偏移",
                extra={"chat": chat_id},
            )
        _reset_compact_tracking(chat_id)
        return
    sessions = CHAT_DELIVERED_OFFSETS.get(chat_id)
    if not sessions:
        return
    if session_key in sessions:
        sessions.pop(session_key, None)
        worker_log.info(
            "清空会话的已处理事件偏移",
            extra={
                "chat": chat_id,
                **_session_extra(key=session_key),
            },
        )
    if not sessions:
        CHAT_DELIVERED_OFFSETS.pop(chat_id, None)
    _reset_compact_tracking(chat_id, session_key)


def _get_delivered_offsets(chat_id: int, session_key: str) -> set[int]:
    return CHAT_DELIVERED_OFFSETS.setdefault(chat_id, {}).setdefault(session_key, set())


async def _deliver_pending_messages(
    chat_id: int,
    session_path: Path,
    *,
    add_completion_header: bool = True
) -> bool:
    """发送待处理的模型消息。

    Args:
        chat_id: Telegram 聊天 ID
        session_path: 会话文件路径
        add_completion_header: 是否添加"✅模型执行完成"前缀（快速轮询阶段为 True，延迟轮询为 False）
    """
    session_key = str(session_path)
    previous_offset = SESSION_OFFSETS.get(session_key, 0)
    new_offset, events = _read_session_events(session_path)
    delivered_response = False
    last_sent = _get_last_message(chat_id, session_key)
    delivered_hashes = _get_delivered_hashes(chat_id, session_key)
    delivered_offsets = _get_delivered_offsets(chat_id, session_key)
    last_committed_offset = previous_offset

    if not events:
        SESSION_OFFSETS[session_key] = max(previous_offset, new_offset)
        return False

    worker_log.info(
        "检测到待发送的模型事件",
        extra={
            **_session_extra(path=session_path),
            "chat": chat_id,
            "events": str(len(events)),
            "offset_before": str(previous_offset),
            "offset_after": str(new_offset),
        },
    )

    for deliverable in events:
        event_offset = deliverable.offset
        text_to_send = (deliverable.text or "").rstrip("\n")
        if event_offset in delivered_offsets:
            worker_log.info(
                "跳过已处理的模型事件",
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                    "offset": str(event_offset),
                },
            )
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            continue
        if not text_to_send:
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            continue
        if deliverable.kind == DELIVERABLE_KIND_PLAN:
            if ENABLE_PLAN_PROGRESS:
                plan_completed = False
                if deliverable.metadata and "plan_completed" in deliverable.metadata:
                    plan_completed = bool(deliverable.metadata.get("plan_completed"))
                worker_log.info(
                    "更新计划进度",
                    extra={
                        **_session_extra(path=session_path),
                        "chat": chat_id,
                        "offset": str(event_offset),
                        "plan_completed": str(plan_completed),
                    },
                )
                await _update_plan_progress(
                    chat_id,
                    text_to_send,
                    plan_completed=plan_completed,
                )
                # 计划事件可能在同一批次后继续跟随模型输出，这里刷新本地状态避免误判
                plan_active = ENABLE_PLAN_PROGRESS and (chat_id in CHAT_PLAN_TEXT)
                plan_completed_flag = bool(CHAT_PLAN_COMPLETION.get(chat_id))
            delivered_offsets.add(event_offset)
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            continue
        if deliverable.kind != DELIVERABLE_KIND_MESSAGE:
            delivered_offsets.add(event_offset)
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            continue
        # 根据轮询阶段决定是否添加完成前缀
        formatted_text = _prepend_completion_header(text_to_send) if add_completion_header else text_to_send
        payload_for_hash = _prepare_model_payload(formatted_text)
        initial_hash = hashlib.sha256(payload_for_hash.encode("utf-8", errors="ignore")).hexdigest()
        if initial_hash in delivered_hashes:
            worker_log.info(
                "跳过重复的模型输出",
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                    "offset": str(event_offset),
                },
            )
            delivered_offsets.add(event_offset)
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            continue
        worker_log.info(
            "准备发送模型输出",
            extra={
                **_session_extra(path=session_path),
                "chat": chat_id,
                "offset": str(event_offset),
                "length": str(len(formatted_text)),
            },
        )
        try:
            delivered_payload = await reply_large_text(chat_id, formatted_text)
        except TelegramBadRequest as exc:
            SESSION_OFFSETS[session_key] = previous_offset
            _clear_last_message(chat_id, session_key)
            worker_log.error(
                "发送消息失败（请求无效）: %s",
                exc,
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                    "offset": event_offset,
                },
            )
            await _notify_send_failure_message(chat_id)
            return False
        except (TelegramNetworkError, TelegramRetryAfter) as exc:
            SESSION_OFFSETS[session_key] = last_committed_offset
            _clear_last_message(chat_id, session_key)
            worker_log.warning(
                "发送消息失败，将重试: %s",
                exc,
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                    "offset": last_committed_offset,
                },
            )
            await _notify_send_failure_message(chat_id)
            return False
        else:
            delivered_response = True
            last_sent = delivered_payload
            final_hash_payload = _prepare_model_payload(delivered_payload or formatted_text)
            message_hash = hashlib.sha256(final_hash_payload.encode("utf-8", errors="ignore")).hexdigest()
            _set_last_message(chat_id, session_key, delivered_payload or formatted_text)
            delivered_hashes.add(initial_hash)
            delivered_hashes.add(message_hash)
            delivered_offsets.add(event_offset)
            CHAT_FAILURE_NOTICES.pop(chat_id, None)
            last_committed_offset = event_offset
            SESSION_OFFSETS[session_key] = event_offset
            worker_log.info(
                "模型输出发送成功",
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                    "offset": str(event_offset),
                    "length": str(len(formatted_text)),
                },
            )
            if session_path is not None:
                await _handle_model_response(
                    chat_id=chat_id,
                    session_key=session_key,
                    session_path=session_path,
                    event_offset=event_offset,
                    content=delivered_payload or formatted_text,
                )
            await _post_delivery_compact_checks(chat_id, session_key)
            if not ENABLE_PLAN_PROGRESS:
                CHAT_PLAN_TEXT.pop(chat_id, None)
                CHAT_PLAN_MESSAGES.pop(chat_id, None)
                CHAT_PLAN_COMPLETION.pop(chat_id, None)

    plan_active = ENABLE_PLAN_PROGRESS and (chat_id in CHAT_PLAN_TEXT)
    plan_completed_flag = bool(CHAT_PLAN_COMPLETION.get(chat_id))
    final_response_sent = session_key in (CHAT_LAST_MESSAGE.get(chat_id) or {})

    if ENABLE_PLAN_PROGRESS and plan_active and plan_completed_flag and final_response_sent:
        await _finalize_plan_progress(chat_id)
        plan_active = False
        plan_completed_flag = False

    if not delivered_response:
        worker_log.info(
            "本轮未发现可发送的模型输出",
            extra={
                **_session_extra(path=session_path),
                "chat": chat_id,
                "offset": str(last_committed_offset),
            },
        )
        SESSION_OFFSETS[session_key] = max(last_committed_offset, new_offset)

    if delivered_response:
        # 实际发送了消息，返回 True 表示本次调用成功发送
        # 这样可以确保延迟轮询机制被正确触发
        if ENABLE_PLAN_PROGRESS and plan_active:
            worker_log.info(
                "模型输出已发送，但计划仍在更新",
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                },
            )
        else:
            worker_log.info(
                "模型输出已发送且计划完成",
                extra={
                    **_session_extra(path=session_path),
                    "chat": chat_id,
                },
            )
        return True

    if ENABLE_PLAN_PROGRESS and not plan_active and final_response_sent:
        worker_log.info(
            "已存在历史响应，计划关闭后确认完成",
            extra={
                **_session_extra(path=session_path),
                "chat": chat_id,
            },
        )
        return True

    return False


async def _ensure_session_watcher(chat_id: int) -> Optional[Path]:
    """确保指定聊天已绑定 Codex 会话并启动监听。"""

    pointer_path: Optional[Path] = None
    if CODEX_SESSION_FILE_PATH:
        pointer_path = resolve_path(CODEX_SESSION_FILE_PATH)

    session_path: Optional[Path] = None
    previous_key = CHAT_SESSION_MAP.get(chat_id)
    if previous_key:
        candidate = resolve_path(previous_key)
        if candidate.exists():
            session_path = candidate
        else:
            worker_log.warning(
                "[session-map] chat=%s 记录的会话文件不存在，准备重新定位",
                chat_id,
                extra={"session": previous_key},
            )

    target_cwd = CODEX_WORKDIR or None

    if session_path is None and pointer_path is not None:
        session_path = _read_pointer_path(pointer_path)
        if session_path is not None:
            worker_log.info(
                "[session-map] chat=%s pointer -> %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )
    if session_path is None and pointer_path is not None:
        latest = _find_latest_rollout_for_cwd(pointer_path, target_cwd)
        if latest is not None:
            session_path = latest
            _update_pointer(pointer_path, latest)
            worker_log.info(
                "[session-map] chat=%s locate latest rollout %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )

    if pointer_path is not None and _is_claudecode_model():
        fallback = _find_latest_claudecode_rollout(pointer_path)
        if fallback is not None and fallback != session_path:
            session_path = fallback
            _update_pointer(pointer_path, session_path)
            worker_log.info(
                "[session-map] chat=%s resume ClaudeCode session %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )

    if session_path is None and pointer_path is not None:
        session_path = await _await_session_path(pointer_path, target_cwd)
        if session_path is not None:
            _update_pointer(pointer_path, session_path)
            worker_log.info(
                "[session-map] chat=%s bind fresh session %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )
    if session_path is None and pointer_path is not None and _is_claudecode_model():
        fallback = _find_latest_claudecode_rollout(pointer_path)
        if fallback is not None:
            session_path = fallback
            _update_pointer(pointer_path, session_path)
            worker_log.info(
                "[session-map] chat=%s fallback bind ClaudeCode session %s",
                chat_id,
                session_path,
                extra=_session_extra(path=session_path),
            )

    if session_path is None:
        worker_log.warning(
            "[session-map] chat=%s 无法确定 Codex 会话",
            chat_id,
        )
        return None

    session_key = str(session_path)
    if session_key not in SESSION_OFFSETS:
        initial_offset = 0
        if session_path.exists():
            try:
                size = session_path.stat().st_size
            except FileNotFoundError:
                size = 0
            backtrack = max(SESSION_INITIAL_BACKTRACK_BYTES, 0)
            initial_offset = max(size - backtrack, 0)
        SESSION_OFFSETS[session_key] = initial_offset
        worker_log.info(
            "[session-map] init offset for %s -> %s",
            session_key,
            SESSION_OFFSETS[session_key],
            extra=_session_extra(key=session_key),
        )

    if previous_key != session_key:
        _clear_last_message(chat_id)
        _reset_compact_tracking(chat_id)
        CHAT_FAILURE_NOTICES.pop(chat_id, None)

    CHAT_SESSION_MAP[chat_id] = session_key

    try:
        delivered = await _deliver_pending_messages(chat_id, session_path)
        if delivered:
            worker_log.info(
                "[session-map] chat=%s 已即时发送 pending 输出",
                chat_id,
                extra=_session_extra(path=session_path),
            )
            return session_path
    except Exception as exc:  # noqa: BLE001
        worker_log.warning(
            "推送后检查 Codex 事件失败: %s",
            exc,
            extra={"chat": chat_id, **_session_extra(path=session_path)},
        )

    watcher = CHAT_WATCHERS.get(chat_id)
    if watcher is not None and not watcher.done():
        return session_path
    if watcher is not None and watcher.done():
        CHAT_WATCHERS.pop(chat_id, None)

    # 中断旧的延迟轮询（如果存在）
    await _interrupt_long_poll(chat_id)

    CHAT_WATCHERS[chat_id] = asyncio.create_task(
        _watch_and_notify(
            chat_id,
            session_path,
            max_wait=WATCH_MAX_WAIT,
            interval=WATCH_INTERVAL,
        )
    )
    return session_path


async def _update_plan_progress(chat_id: int, plan_text: str, *, plan_completed: bool) -> bool:
    if not ENABLE_PLAN_PROGRESS:
        return False
    CHAT_PLAN_COMPLETION[chat_id] = plan_completed
    if CHAT_PLAN_TEXT.get(chat_id) == plan_text:
        worker_log.debug(
            "计划进度内容未变化，跳过更新",
            extra={"chat": chat_id},
        )
        return True

    bot = current_bot()
    message_id = CHAT_PLAN_MESSAGES.get(chat_id)
    parse_mode = _plan_parse_mode_value()

    if message_id is None:
        sent_message: Optional[Message] = None

        async def _send_plan_payload(payload: str) -> None:
            nonlocal sent_message

            async def _do() -> None:
                nonlocal sent_message
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=payload,
                    parse_mode=parse_mode,
                    disable_notification=True,
                )

            await _send_with_retry(_do)

        async def _send_plan_payload_raw(payload: str) -> None:
            nonlocal sent_message

            async def _do() -> None:
                nonlocal sent_message
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=payload,
                    parse_mode=None,
                    disable_notification=True,
                )

            await _send_with_retry(_do)

        try:
            await _send_with_markdown_guard(
                plan_text,
                _send_plan_payload,
                raw_sender=_send_plan_payload_raw,
            )
        except TelegramBadRequest as exc:
            worker_log.warning(
                "计划进度发送失败，将停止更新: %s",
                exc,
                extra={"chat": chat_id},
            )
            return False
        except (TelegramNetworkError, TelegramRetryAfter) as exc:
            worker_log.warning(
                "计划进度发送遇到网络异常: %s",
                exc,
                extra={"chat": chat_id},
            )
            return False

        if sent_message is None:
            return False

        message_id = sent_message.message_id
        CHAT_PLAN_MESSAGES[chat_id] = message_id
        worker_log.info(
            "计划进度消息已发送",
            extra={
                "chat": chat_id,
                "message_id": message_id,
                "length": len(plan_text),
            },
        )
    else:
        async def _edit_payload(payload: str) -> None:

            async def _do() -> None:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=payload,
                    parse_mode=parse_mode,
                )

            await _send_with_retry(_do)

        async def _edit_payload_raw(payload: str) -> None:

            async def _do() -> None:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=payload,
                    parse_mode=None,
                )

            await _send_with_retry(_do)

        try:
            await _send_with_markdown_guard(
                plan_text,
                _edit_payload,
                raw_sender=_edit_payload_raw,
            )
        except TelegramBadRequest as exc:
            CHAT_PLAN_TEXT.pop(chat_id, None)
            removed_id = CHAT_PLAN_MESSAGES.pop(chat_id, None)
            worker_log.warning(
                "计划进度编辑失败，将停止更新: %s",
                exc,
                extra={"chat": chat_id, "message_id": removed_id},
            )
            return False
        except (TelegramNetworkError, TelegramRetryAfter) as exc:
            worker_log.warning(
                "计划进度编辑遇到网络异常: %s",
                exc,
                extra={"chat": chat_id, "message_id": message_id},
            )
            return False
        worker_log.info(
            "计划进度消息已编辑",
            extra={
                "chat": chat_id,
                "message_id": message_id,
                "length": len(plan_text),
            },
        )

    CHAT_PLAN_TEXT[chat_id] = plan_text
    return True


async def _finalize_plan_progress(chat_id: int) -> None:
    CHAT_PLAN_TEXT.pop(chat_id, None)
    CHAT_PLAN_MESSAGES.pop(chat_id, None)
    CHAT_PLAN_COMPLETION.pop(chat_id, None)




async def _interrupt_long_poll(chat_id: int) -> None:
    """
    中断指定 chat 的延迟轮询。

    当用户发送新消息时调用，确保旧的延迟轮询被终止，
    为新的监听任务让路。

    线程安全：使用 asyncio.Lock 保护状态访问。
    """
    if CHAT_LONG_POLL_LOCK is None:
        # 锁未初始化（测试环境或启动早期）
        return

    async with CHAT_LONG_POLL_LOCK:
        state = CHAT_LONG_POLL_STATE.get(chat_id)
        if state is not None:
            state["interrupted"] = True
            worker_log.info(
                "标记延迟轮询为待中断",
                extra={"chat": chat_id},
            )


async def _watch_and_notify(chat_id: int, session_path: Path,
                            max_wait: float, interval: float):
    """
    监听会话文件并发送消息。

    两阶段轮询机制：
    - 阶段1（快速轮询）：interval 间隔（通常 0.3 秒），直到首次发送成功
    - 阶段2（延迟轮询）：3 秒间隔，最多 600 次（持续 30 分钟），捕获长时间任务的后续输出

    异常安全：使用 try...finally 确保状态清理。
    中断机制：收到新 Telegram 消息时会设置 interrupted 标志，轮询自动停止。
    """
    start = time.monotonic()
    first_delivery_done = False
    current_interval = interval  # 初始为快速轮询间隔（0.3 秒）
    long_poll_rounds = 0
    long_poll_max_rounds = 600  # 30 分钟 / 3 秒 = 600 次
    long_poll_interval = 3.0  # 3 秒

    try:
        while True:
            # 检查是否被新消息中断（使用锁保护）
            if CHAT_LONG_POLL_LOCK is not None:
                async with CHAT_LONG_POLL_LOCK:
                    state = CHAT_LONG_POLL_STATE.get(chat_id)
                    if state is not None and state.get("interrupted", False):
                        worker_log.info(
                            "延迟轮询被新消息中断",
                            extra={
                                **_session_extra(path=session_path),
                                "chat": chat_id,
                                "round": long_poll_rounds,
                            },
                        )
                        return

            await asyncio.sleep(current_interval)

            # 检查超时（仅在快速轮询阶段）
            if not first_delivery_done and max_wait > 0 and time.monotonic() - start > max_wait:
                worker_log.warning(
                    "[session-map] chat=%s 长时间未获取到 Codex 输出，停止轮询",
                    chat_id,
                    extra=_session_extra(path=session_path),
                )
                return

            if not session_path.exists():
                continue

            try:
                # 快速轮询阶段添加前缀，延迟轮询阶段不添加
                delivered = await _deliver_pending_messages(
                    chat_id,
                    session_path,
                    add_completion_header=not first_delivery_done
                )
            except Exception as exc:
                worker_log.error(
                    "消息发送时发生未预期异常",
                    exc_info=exc,
                    extra={
                        **_session_extra(path=session_path),
                        "chat": chat_id,
                    },
                )
                delivered = False

            # 首次发送成功，切换到延迟轮询模式
            if delivered and not first_delivery_done:
                first_delivery_done = True
                current_interval = long_poll_interval
                if CHAT_LONG_POLL_LOCK is not None:
                    async with CHAT_LONG_POLL_LOCK:
                        CHAT_LONG_POLL_STATE[chat_id] = {
                            "active": True,
                            "round": 0,
                            "max_rounds": long_poll_max_rounds,
                            "interrupted": False,
                        }
                worker_log.info(
                    "首次发送成功，启动延迟轮询模式",
                    extra={
                        **_session_extra(path=session_path),
                        "chat": chat_id,
                        "interval": long_poll_interval,
                        "max_rounds": long_poll_max_rounds,
                    },
                )
                continue

            # 延迟轮询阶段
            if first_delivery_done:
                if delivered:
                    # 又收到新消息，重置轮询计数
                    long_poll_rounds = 0
                    if CHAT_LONG_POLL_LOCK is not None:
                        async with CHAT_LONG_POLL_LOCK:
                            state = CHAT_LONG_POLL_STATE.get(chat_id)
                            if state is not None:
                                state["round"] = 0
                    worker_log.info(
                        "延迟轮询中收到新消息，重置计数",
                        extra={
                            **_session_extra(path=session_path),
                            "chat": chat_id,
                        },
                    )
                else:
                    # 无新消息，增加轮询计数
                    long_poll_rounds += 1
                    if CHAT_LONG_POLL_LOCK is not None:
                        async with CHAT_LONG_POLL_LOCK:
                            state = CHAT_LONG_POLL_STATE.get(chat_id)
                            if state is not None:
                                state["round"] = long_poll_rounds

                    if long_poll_rounds >= long_poll_max_rounds:
                        worker_log.info(
                            "延迟轮询达到最大次数，停止监听",
                            extra={
                                **_session_extra(path=session_path),
                                "chat": chat_id,
                                "total_rounds": long_poll_rounds,
                            },
                        )
                        return

                    worker_log.debug(
                        "延迟轮询中无新消息",
                        extra={
                            **_session_extra(path=session_path),
                            "chat": chat_id,
                            "round": f"{long_poll_rounds}/{long_poll_max_rounds}",
                        },
                    )
                continue

            # 快速轮询阶段：如果已发送消息，退出
            if delivered:
                return

    finally:
        # 确保无论如何都清理延迟轮询状态
        if CHAT_LONG_POLL_LOCK is not None:
            async with CHAT_LONG_POLL_LOCK:
                if chat_id in CHAT_LONG_POLL_STATE:
                    CHAT_LONG_POLL_STATE.pop(chat_id, None)
                    worker_log.debug(
                        "监听任务退出，已清理延迟轮询状态",
                        extra={"chat": chat_id},
                    )


def _read_pointer_path(pointer: Path) -> Optional[Path]:
    try:
        raw = pointer.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not raw:
        return None
    rollout = resolve_path(raw)
    return rollout if rollout.exists() else None


def _read_session_meta_cwd(path: Path) -> Optional[str]:
    try:
        with path.open(encoding="utf-8", errors="ignore") as fh:
            first_line = fh.readline()
    except OSError:
        return None
    if not first_line:
        return None
    try:
        data = json.loads(first_line)
    except json.JSONDecodeError:
        return None
    payload = data.get("payload") or {}
    return payload.get("cwd")


def _find_latest_claudecode_rollout(pointer: Path) -> Optional[Path]:
    """ClaudeCode 专用：在缺少 cwd 元数据时按更新时间选择最新会话文件。"""

    pointer_target = _read_pointer_path(pointer)
    candidates: List[Path] = []
    if pointer_target is not None:
        candidates.append(pointer_target)

    search_roots: List[Path] = []
    if MODEL_SESSION_ROOT:
        search_roots.append(resolve_path(MODEL_SESSION_ROOT))
    if pointer_target is not None:
        search_roots.append(pointer_target.parent)
    search_roots.append(pointer.parent)
    search_roots.append(pointer.parent / "sessions")

    seen_roots: set[str] = set()
    pattern = f"**/{MODEL_SESSION_GLOB}"
    for root in search_roots:
        try:
            real_root = root.resolve()
        except OSError:
            real_root = root
        key = str(real_root)
        if key in seen_roots:
            continue
        seen_roots.add(key)
        if not real_root.exists():
            continue
        for rollout in real_root.glob(pattern):
            if rollout.is_file():
                candidates.append(rollout)

    latest_path: Optional[Path] = None
    latest_mtime = -1.0
    seen_files: set[str] = set()
    for rollout in candidates:
        try:
            real_rollout = rollout.resolve()
        except OSError:
            real_rollout = rollout
        key = str(real_rollout)
        if key in seen_files:
            continue
        seen_files.add(key)
        try:
            mtime = real_rollout.stat().st_mtime
        except OSError:
            continue
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_path = Path(real_rollout)

    return latest_path


def _find_latest_rollout_for_cwd(pointer: Path, target_cwd: Optional[str]) -> Optional[Path]:
    """依据目标 CWD 在候选目录中寻找最新会话文件。"""

    roots: List[Path] = []
    for candidate in (CODEX_SESSIONS_ROOT, MODEL_SESSION_ROOT):
        if candidate:
            roots.append(resolve_path(candidate))

    pointer_target = _read_pointer_path(pointer)
    if pointer_target is not None:
        roots.append(pointer_target.parent)
        for parent in pointer_target.parents:
            if parent.name == "sessions":
                roots.append(parent)
                break

    roots.append(pointer.parent / "sessions")

    latest_path: Optional[Path] = None
    latest_mtime = -1.0
    seen: set[str] = set()

    for root in roots:
        try:
            real_root = root.resolve()
        except OSError:
            real_root = root
        key = str(real_root)
        if key in seen:
            continue
        seen.add(key)
        if not real_root.exists():
            continue

        pattern = f"**/{MODEL_SESSION_GLOB}"
        for rollout in real_root.glob(pattern):
            if not rollout.is_file():
                continue
            try:
                resolved = str(rollout.resolve())
            except OSError:
                resolved = str(rollout)
            try:
                mtime = rollout.stat().st_mtime
            except OSError:
                continue
            if mtime <= latest_mtime:
                continue
            if target_cwd:
                cwd = _read_session_meta_cwd(rollout)
                if cwd != target_cwd:
                    continue
            latest_mtime = mtime
            latest_path = rollout

    return latest_path


async def _await_session_path(
    pointer: Optional[Path], target_cwd: Optional[str], poll: float = 0.5
) -> Optional[Path]:
    if pointer:
        candidate = _read_pointer_path(pointer)
        if candidate is not None:
            return candidate
    await asyncio.sleep(poll)
    if pointer:
        candidate = _read_pointer_path(pointer)
        if candidate is not None:
            return candidate
        return _find_latest_rollout_for_cwd(pointer, target_cwd)
    return None


def _update_pointer(pointer: Path, rollout: Path) -> None:
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(rollout), encoding="utf-8")


def _format_plan_update(arguments: Any, *, event_timestamp: Optional[str]) -> Optional[Tuple[str, bool]]:
    if not isinstance(arguments, str):
        return None
    try:
        data = json.loads(arguments)
    except (TypeError, json.JSONDecodeError):
        return None

    plan_items = data.get("plan")
    if not isinstance(plan_items, list):
        return None

    explanation = data.get("explanation")
    lines: List[str] = []
    if isinstance(explanation, str) and explanation.strip():
        lines.append(explanation.strip())

    steps: List[str] = []
    all_completed = True
    for idx, item in enumerate(plan_items, 1):
        if not isinstance(item, dict):
            continue
        step = item.get("step")
        if not isinstance(step, str) or not step.strip():
            continue
        status_raw = str(item.get("status", "")).strip().lower()
        status_icon = PLAN_STATUS_LABELS.get(status_raw, status_raw or "-")
        steps.append(f"{status_icon} {idx}. {step.strip()}")
        if status_raw != "completed":
            all_completed = False

    if not steps:
        return None

    header = "当前任务执行计划："
    body_parts = [header]
    if lines:
        body_parts.extend(lines)
    body_parts.extend(steps)
    text = "\n".join(body_parts)
    if event_timestamp:
        tz_name = os.environ.get("LOG_TIMEZONE", "Asia/Shanghai").strip() or "Asia/Shanghai"
        formatted_ts: Optional[str] = None
        try:
            normalized = event_timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            try:
                target_tz = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                target_tz = ZoneInfo("Asia/Shanghai")
            formatted_ts = dt.astimezone(target_tz).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_ts = None
        suffix = formatted_ts or event_timestamp
        text = f"{text}\n\n状态更新中，最后更新时间：{suffix}"
    return text, all_completed


def _extract_codex_payload(data: dict, *, event_timestamp: Optional[str]) -> Optional[Tuple[str, str, Optional[Dict[str, Any]]]]:
    event_type = data.get("type")

    if event_type == "agent_message":
        message = data.get("message")
        if isinstance(message, str) and message.strip():
            return DELIVERABLE_KIND_MESSAGE, message, None

    if event_type == "event_msg":
        payload = data.get("payload") or {}
        if payload.get("type") == "agent_message":
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return DELIVERABLE_KIND_MESSAGE, message, None
        return None

    if event_type != "response_item":
        return None

    payload = data.get("payload") or {}
    payload_type = payload.get("type")

    if payload_type in {"message", "assistant_message"}:
        content = payload.get("content")
        if isinstance(content, list):
            fragments = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") in {"output_text", "text", "markdown"}:
                    text = item.get("text") or item.get("markdown")
                    if text:
                        fragments.append(text)
            if fragments:
                return DELIVERABLE_KIND_MESSAGE, "\n".join(fragments), None
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return DELIVERABLE_KIND_MESSAGE, message, None
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return DELIVERABLE_KIND_MESSAGE, text, None

    if payload_type == "function_call" and payload.get("name") == "update_plan":
        plan_result = _format_plan_update(payload.get("arguments"), event_timestamp=event_timestamp)
        if plan_result:
            plan_text, plan_completed = plan_result
            extra: Dict[str, Any] = {"plan_completed": plan_completed}
            call_id = payload.get("call_id")
            if call_id:
                extra["call_id"] = call_id
            return DELIVERABLE_KIND_PLAN, plan_text, extra

    if payload.get("event") == "final":
        delta = payload.get("delta")
        if isinstance(delta, str) and delta.strip():
            return DELIVERABLE_KIND_MESSAGE, delta, None

    return None


def _extract_claudecode_payload(
    data: dict, *, event_timestamp: Optional[str]
) -> Optional[Tuple[str, str, Optional[Dict[str, Any]]]]:
    # Claude Code 在启动时会输出 isSidechain=true 的欢迎语，此类事件直接忽略
    sidechain_flag = data.get("isSidechain")
    if isinstance(sidechain_flag, bool) and sidechain_flag:
        return None

    event_type = data.get("type")

    if event_type == "assistant":
        message = data.get("message")
        if isinstance(message, dict):
            fragments: List[str] = []
            content = message.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("type")
                    if item_type != "text":
                        continue
                    text_value = item.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        fragments.append(text_value)
                if fragments:
                    combined = "\n\n".join(fragments)
                    metadata: Optional[Dict[str, Any]] = None
                    message_id = message.get("id")
                    if isinstance(message_id, str) and message_id:
                        metadata = {"message_id": message_id}
                    return DELIVERABLE_KIND_MESSAGE, combined, metadata
            fallback_text = message.get("text")
            if isinstance(fallback_text, str) and fallback_text.strip():
                metadata: Optional[Dict[str, Any]] = None
                message_id = message.get("id")
                if isinstance(message_id, str) and message_id:
                    metadata = {"message_id": message_id}
                return DELIVERABLE_KIND_MESSAGE, fallback_text, metadata
        return None

    return _extract_codex_payload(data, event_timestamp=event_timestamp)


def _extract_deliverable_payload(data: dict, *, event_timestamp: Optional[str]) -> Optional[Tuple[str, str, Optional[Dict[str, Any]]]]:
    if _is_claudecode_model():
        return _extract_claudecode_payload(data, event_timestamp=event_timestamp)
    return _extract_codex_payload(data, event_timestamp=event_timestamp)


def _read_session_events(path: Path) -> Tuple[int, List[SessionDeliverable]]:
    key = str(path)
    offset = SESSION_OFFSETS.get(key)
    if offset is None:
        try:
            offset = path.stat().st_size
        except FileNotFoundError:
            offset = 0
        SESSION_OFFSETS[key] = offset
    events: List[SessionDeliverable] = []
    new_offset = offset

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            fh.seek(offset)
            while True:
                line = fh.readline()
                if not line:
                    break
                new_offset = fh.tell()
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_timestamp = event.get("timestamp")
                if not isinstance(event_timestamp, str):
                    event_timestamp = None
                candidate = _extract_deliverable_payload(event, event_timestamp=event_timestamp)
                if candidate:
                    kind, text, extra = candidate
                    events.append(
                        SessionDeliverable(
                            offset=new_offset,
                            kind=kind,
                            text=text,
                            timestamp=event_timestamp,
                            metadata=extra,
                        )
                    )
    except FileNotFoundError:
        return offset, []

    return new_offset, events


# --- 处理器 ---

@router.message(Command("help"))
async def on_help_command(message: Message) -> None:
    text = (
        "*指令总览*\n"
        "- /help — 查看全部命令\n"
        "- /tasks — 任务管理命令清单\n"
        "- /task_new — 创建任务（交互式或附带参数）\n"
        "- /task_list — 查看任务列表，支持 status/limit/offset\n"
        "- /task_show — 查看某个任务详情\n"
        "- /task_update — 快速更新任务字段\n"
        "- /task_note — 添加任务备注\n"
        "- /task_delete — 归档或恢复任务\n"
        "- 子任务功能已下线，请使用 /task_new 创建新的任务\n\n"
        "提示：大部分操作都提供按钮和多轮对话引导，无需记忆复杂参数。"
    )
    await _answer_with_markdown(message, text)


@router.message(Command("tasks"))
async def on_tasks_help(message: Message) -> None:
    text = (
        "*任务管理命令*\n"
        "- /task_new 标题 | type=需求 — 创建任务\n"
        "- /task_list [status=test] [limit=10] [offset=0] — 列出任务\n"
        "- /task_show TASK_0001 — 查看详情\n"
        "- /task_update TASK_0001 status=test | priority=2 | type=缺陷 — 更新字段\n"
        "- /task_note TASK_0001 备注内容 | type=research — 添加备注\n"
        "- /task_delete TASK_0001 — 归档任务（再次执行可恢复）\n"
        "- 子任务功能已下线，请使用 /task_new 创建新的任务\n\n"
        "建议：使用 `/task_new`、`/task_show` 等命令触发后按按钮完成后续步骤。"
    )
    await _answer_with_markdown(message, text)


def _normalize_status(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    token = _canonical_status_token(value, quiet=True)
    return token if token in TASK_STATUSES else None


def _normalize_task_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = _strip_number_prefix((value or "").strip())
    if not raw:
        return None
    cleaned = _strip_task_type_emoji(raw)
    if not cleaned:
        return None
    token = cleaned.lower()
    if token in TASK_TYPES:
        return token
    if cleaned in TASK_TYPE_LABELS.values():
        for code, label in TASK_TYPE_LABELS.items():
            if cleaned == label:
                return code
    alias = _TASK_TYPE_ALIAS.get(cleaned) or _TASK_TYPE_ALIAS.get(token)
    if alias in TASK_TYPES:
        return alias
    return None

def _actor_from_message(message: Message) -> str:
    if message.from_user and message.from_user.full_name:
        return f"{message.from_user.full_name}#{message.from_user.id}"
    return str(message.from_user.id if message.from_user else message.chat.id)


def _actor_from_callback(callback: CallbackQuery) -> str:
    user = callback.from_user
    if user and user.full_name:
        return f"{user.full_name}#{user.id}"
    if user:
        return str(user.id)
    if callback.message and callback.message.chat:
        return str(callback.message.chat.id)
    return "unknown"


async def _build_task_list_view(
    *,
    status: Optional[str],
    page: int,
    limit: int,
) -> tuple[str, InlineKeyboardMarkup]:
    exclude_statuses: Optional[Sequence[str]] = None if status else ("done",)
    tasks, total_pages = await TASK_SERVICE.paginate(
        status=status,
        page=page,
        page_size=limit,
        exclude_statuses=exclude_statuses,
    )
    total = await TASK_SERVICE.count_tasks(
        status=status,
        include_archived=False,
        exclude_statuses=exclude_statuses,
    )
    display_pages = total_pages or 1
    current_page_display = min(page, display_pages)
    lines = [
        "*任务列表*",
        f"筛选状态：{_format_status(status) if status else '全部'}",
    ]
    if not tasks:
        lines.append("当前没有匹配的任务，可使用上方状态按钮切换。")
    lines.append(
        f"分页信息：页码 {current_page_display}/{display_pages} · 每页 {limit} 条 · 总数 {total}"
    )
    text = "\n".join(lines)

    rows: list[list[InlineKeyboardButton]] = []
    rows.extend(_build_status_filter_row(status, limit))
    for task in tasks:
        label = _compose_task_button_label(task)
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"task:detail:{task.id}",
                )
            ]
        )

    status_token = status or "-"
    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"task:list_page:{status_token}:{page-1}:{limit}",
            )
        )
    if total_pages and page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"task:list_page:{status_token}:{page+1}:{limit}",
            )
        )
    if nav_row:
        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="🔍 搜索任务",
                callback_data=f"{TASK_LIST_SEARCH_CALLBACK}:{status_token}:{page}:{limit}",
            ),
            InlineKeyboardButton(
                text="➕ 创建任务",
                callback_data=TASK_LIST_CREATE_CALLBACK,
            ),
        ]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return text, markup


async def _build_task_search_view(
    keyword: str,
    *,
    page: int,
    limit: int,
    origin_status: Optional[str],
    origin_page: int,
) -> tuple[str, InlineKeyboardMarkup]:
    tasks, total_pages, total = await TASK_SERVICE.search_tasks(
        keyword,
        page=page,
        page_size=limit,
    )
    display_pages = total_pages or 1
    current_page_display = min(page, display_pages)
    sanitized_keyword = keyword.replace("\n", " ").strip()
    if not sanitized_keyword:
        sanitized_keyword = "-"
    # 修复：避免双重转义
    if _IS_MARKDOWN_V2:
        escaped_keyword = sanitized_keyword
    else:
        escaped_keyword = _escape_markdown_text(sanitized_keyword)
    lines = [
        "*任务搜索结果*",
        f"搜索关键词：{escaped_keyword}",
        "搜索范围：标题、描述",
        f"分页信息：页码 {current_page_display}/{display_pages} · 每页 {limit} 条 · 总数 {total}",
    ]
    if not tasks:
        lines.append("未找到匹配的任务，请调整关键词或重新搜索。")

    rows: list[list[InlineKeyboardButton]] = []
    for task in tasks:
        label = _compose_task_button_label(task)
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"task:detail:{task.id}",
                )
            ]
        )

    encoded_keyword = quote(keyword, safe="")
    origin_status_token = origin_status or "-"

    nav_row: list[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=(
                    f"{TASK_LIST_SEARCH_PAGE_CALLBACK}:{encoded_keyword}:"
                    f"{origin_status_token}:{origin_page}:{page-1}:{limit}"
                ),
            )
        )
    if total_pages and page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=(
                    f"{TASK_LIST_SEARCH_PAGE_CALLBACK}:{encoded_keyword}:"
                    f"{origin_status_token}:{origin_page}:{page+1}:{limit}"
                ),
            )
        )
    if nav_row:
        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="🔁 重新搜索",
                callback_data=f"{TASK_LIST_SEARCH_CALLBACK}:{origin_status_token}:{origin_page}:{limit}",
            ),
            InlineKeyboardButton(
                text="📋 返回列表",
                callback_data=f"{TASK_LIST_RETURN_CALLBACK}:{origin_status_token}:{origin_page}:{limit}",
            ),
        ]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    text = "\n".join(lines)
    return text, markup


async def _handle_task_list_request(message: Message) -> None:
    raw_text = (message.text or "").strip()
    args = _extract_command_args(raw_text) if raw_text.startswith("/") else ""
    _, extra = parse_structured_text(args)
    status = _normalize_status(extra.get("status"))
    try:
        limit = int(extra.get("limit", DEFAULT_PAGE_SIZE))
    except ValueError:
        limit = DEFAULT_PAGE_SIZE
    limit = max(1, min(limit, 50))
    try:
        page = int(extra.get("page", "1"))
    except ValueError:
        page = 1
    page = max(page, 1)

    text, markup = await _build_task_list_view(status=status, page=page, limit=limit)
    sent = await _answer_with_markdown(message, text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(
            sent,
            _make_list_view_state(status=status, page=page, limit=limit),
        )


@router.message(Command("task_list"))
async def on_task_list(message: Message) -> None:
    await _handle_task_list_request(message)


@router.message(F.text == WORKER_MENU_BUTTON_TEXT)
async def on_task_list_button(message: Message) -> None:
    await _handle_task_list_request(message)


async def _dispatch_task_new_command(source_message: Message, actor: Optional[User]) -> None:
    """模拟用户输入 /task_new，让现有命令逻辑复用。"""
    if actor is None:
        raise ValueError("缺少有效的任务创建用户信息")
    bot_instance = current_bot()
    command_text = "/task_new"
    try:
        now = datetime.now(tz=ZoneInfo("UTC"))
    except ZoneInfoNotFoundError:
        now = datetime.now(UTC)
    entities = [
        MessageEntity(type="bot_command", offset=0, length=len(command_text)),
    ]
    synthetic_message = source_message.model_copy(
        update={
            "message_id": source_message.message_id + 1,
            "date": now,
            "edit_date": None,
            "text": command_text,
            "from_user": actor,
            "entities": entities,
        }
    )
    update = Update.model_construct(
        update_id=int(time.time() * 1000),
        message=synthetic_message,
    )
    await dp.feed_update(bot_instance, update)


@router.message(F.text == WORKER_CREATE_TASK_BUTTON_TEXT)
async def on_task_create_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        await _dispatch_task_new_command(message, message.from_user)
    except ValueError:
        await message.answer("无法发起任务创建，请重试或使用 /task_new 命令。")


@router.callback_query(F.data.startswith("task:list_page:"))
async def on_task_list_page(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("回调数据异常", show_alert=True)
        return
    _, _, status_token, page_raw, limit_raw = parts
    if callback.message is None:
        await callback.answer("无法定位原始消息", show_alert=True)
        return
    status = None if status_token == "-" else _normalize_status(status_token)
    try:
        page = int(page_raw)
        limit = int(limit_raw)
    except ValueError:
        await callback.answer("分页参数错误", show_alert=True)
        return
    page = max(page, 1)
    limit = max(1, min(limit, 50))
    text, markup = await _build_task_list_view(status=status, page=page, limit=limit)
    state = _make_list_view_state(status=status, page=page, limit=limit)
    if await _try_edit_message(callback.message, text, reply_markup=markup):
        _set_task_view_context(callback.message, state)
    else:
        origin = callback.message
        origin_chat = getattr(origin, "chat", None)
        if origin and origin_chat:
            _clear_task_view(origin_chat.id, origin.message_id)
        sent = await _answer_with_markdown(origin or callback.message, text, reply_markup=markup)
        if sent is not None:
            _init_task_view_context(sent, state)
    await callback.answer()


@router.callback_query(F.data.startswith(f"{TASK_LIST_SEARCH_CALLBACK}:"))
async def on_task_list_search(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("回调数据异常", show_alert=True)
        return
    _, _, status_token, page_raw, limit_raw = parts
    status = None if status_token == "-" else _normalize_status(status_token)
    try:
        page = max(int(page_raw), 1)
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        await callback.answer("参数错误", show_alert=True)
        return
    await state.clear()
    await state.update_data(
        origin_status=status,
        origin_status_token=status_token,
        origin_page=page,
        limit=limit,
        origin_message=callback.message,
    )
    await state.set_state(TaskListSearchStates.waiting_keyword)
    await callback.answer("请输入搜索关键词")
    if callback.message:
        await _prompt_task_search_keyword(callback.message)


@router.callback_query(F.data.startswith(f"{TASK_LIST_SEARCH_PAGE_CALLBACK}:"))
async def on_task_list_search_page(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 7:
        await callback.answer("回调数据异常", show_alert=True)
        return
    _, _, encoded_keyword, origin_status_token, origin_page_raw, target_page_raw, limit_raw = parts
    if callback.message is None:
        await callback.answer("无法定位原始消息", show_alert=True)
        return
    keyword = unquote(encoded_keyword)
    origin_status = None if origin_status_token == "-" else _normalize_status(origin_status_token)
    try:
        origin_page = max(int(origin_page_raw), 1)
        page = max(int(target_page_raw), 1)
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        await callback.answer("参数错误", show_alert=True)
        return
    text, markup = await _build_task_search_view(
        keyword,
        page=page,
        limit=limit,
        origin_status=origin_status,
        origin_page=origin_page,
    )
    view_state = _make_search_view_state(
        keyword=keyword,
        page=page,
        limit=limit,
        origin_status=origin_status,
        origin_page=origin_page,
    )
    if await _try_edit_message(callback.message, text, reply_markup=markup):
        _set_task_view_context(callback.message, view_state)
    else:
        origin = callback.message
        origin_chat = getattr(origin, "chat", None)
        if origin and origin_chat:
            _clear_task_view(origin_chat.id, origin.message_id)
        sent = await _answer_with_markdown(origin or callback.message, text, reply_markup=markup)
        if sent is not None:
            _init_task_view_context(sent, view_state)
    await callback.answer()


@router.callback_query(F.data.startswith(f"{TASK_LIST_RETURN_CALLBACK}:"))
async def on_task_list_return(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("回调数据异常", show_alert=True)
        return
    _, _, status_token, page_raw, limit_raw = parts
    if callback.message is None:
        await callback.answer("无法定位原始消息", show_alert=True)
        return
    status = None if status_token == "-" else _normalize_status(status_token)
    try:
        page = max(int(page_raw), 1)
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        await callback.answer("参数错误", show_alert=True)
        return
    await state.clear()
    text, markup = await _build_task_list_view(status=status, page=page, limit=limit)
    view_state = _make_list_view_state(status=status, page=page, limit=limit)
    if await _try_edit_message(callback.message, text, reply_markup=markup):
        _set_task_view_context(callback.message, view_state)
    else:
        origin = callback.message
        origin_chat = getattr(origin, "chat", None)
        if origin and origin_chat:
            _clear_task_view(origin_chat.id, origin.message_id)
        sent = await _answer_with_markdown(origin or callback.message, text, reply_markup=markup)
        if sent is not None:
            _init_task_view_context(sent, view_state)
    await callback.answer("已返回任务列表")


@router.callback_query(F.data == TASK_LIST_CREATE_CALLBACK)
async def on_task_list_create(callback: CallbackQuery) -> None:
    message = callback.message
    user = callback.from_user
    if message is None or user is None:
        await callback.answer("无法定位会话", show_alert=True)
        return
    await callback.answer()
    await _dispatch_task_new_command(message, user)


@router.message(TaskListSearchStates.waiting_keyword)
async def on_task_list_search_keyword(message: Message, state: FSMContext) -> None:
    raw_text = message.text or ""
    trimmed = raw_text.strip()
    options = [SKIP_TEXT, "取消"]
    resolved = _resolve_reply_choice(raw_text, options=options)
    data = await state.get_data()
    origin_status = data.get("origin_status")
    origin_page = int(data.get("origin_page", 1) or 1)
    limit = int(data.get("limit", DEFAULT_PAGE_SIZE) or DEFAULT_PAGE_SIZE)
    limit = max(1, min(limit, 50))
    origin_message = data.get("origin_message")

    async def _restore_list() -> None:
        text, markup = await _build_task_list_view(status=origin_status, page=origin_page, limit=limit)
        list_state = _make_list_view_state(status=origin_status, page=origin_page, limit=limit)
        if await _try_edit_message(origin_message, text, reply_markup=markup):
            _set_task_view_context(origin_message, list_state)
            return
        origin_chat = getattr(origin_message, "chat", None)
        if origin_message and origin_chat:
            _clear_task_view(origin_chat.id, origin_message.message_id)
        sent = await _answer_with_markdown(message, text, reply_markup=markup)
        if sent is not None:
            _init_task_view_context(sent, list_state)

    if resolved == "取消" or resolved == SKIP_TEXT or not trimmed:
        await state.clear()
        await _restore_list()
        await message.answer("已返回任务列表。", reply_markup=_build_worker_main_keyboard())
        return

    if len(trimmed) < SEARCH_KEYWORD_MIN_LENGTH:
        await message.answer(
            f"关键词长度至少 {SEARCH_KEYWORD_MIN_LENGTH} 个字符，请重新输入：",
            reply_markup=_build_description_keyboard(),
        )
        return
    if len(trimmed) > SEARCH_KEYWORD_MAX_LENGTH:
        await message.answer(
            f"关键词长度不可超过 {SEARCH_KEYWORD_MAX_LENGTH} 个字符，请重新输入：",
            reply_markup=_build_description_keyboard(),
        )
        return

    search_text, search_markup = await _build_task_search_view(
        trimmed,
        page=1,
        limit=limit,
        origin_status=origin_status,
        origin_page=origin_page,
    )
    await state.clear()
    search_state = _make_search_view_state(
        keyword=trimmed,
        page=1,
        limit=limit,
        origin_status=origin_status,
        origin_page=origin_page,
    )
    if await _try_edit_message(origin_message, search_text, reply_markup=search_markup):
        _set_task_view_context(origin_message, search_state)
    else:
        origin_chat = getattr(origin_message, "chat", None)
        if origin_message and origin_chat:
            _clear_task_view(origin_chat.id, origin_message.message_id)
        sent = await _answer_with_markdown(message, search_text, reply_markup=search_markup)
        if sent is not None:
            _init_task_view_context(sent, search_state)
    await message.answer("搜索完成，已展示结果。", reply_markup=_build_worker_main_keyboard())


@router.message(Command("task_show"))
async def on_task_show(message: Message) -> None:
    args = _extract_command_args(message.text)
    if not args:
        await _answer_with_markdown(message, "用法：/task_show TASK_0001")
        return
    task_id = _normalize_task_id(args)
    if not task_id:
        await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
        return
    await _reply_task_detail_message(message, task_id)


@router.message(F.text.regexp(r"^/TASK_[A-Z0-9_]+(?:@[\w_]+)?(?:\s|$)"))
async def on_task_quick_command(message: Message) -> None:
    """处理直接使用 /TASK_XXXX 调用的快捷查询命令。"""
    raw_text = (message.text or "").strip()
    if not raw_text:
        await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
        return
    first_token = raw_text.split()[0]
    task_id = _normalize_task_id(first_token)
    if not task_id:
        await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
        return
    await _reply_task_detail_message(message, task_id)


@router.message(Command("task_children"))
async def on_task_children(message: Message) -> None:
    await _answer_with_markdown(
        message,
        "子任务功能已下线，历史子任务已自动归档。请使用 /task_new 创建独立任务以拆分工作。",
    )


@router.message(Command("task_new"))
async def on_task_new(message: Message, state: FSMContext) -> None:
    args = _extract_command_args(message.text)
    if args:
        title, extra = parse_structured_text(args)
        title = title.strip()
        if not title:
            await _answer_with_markdown(message, "请提供任务标题，例如：/task_new 修复登录 | type=需求")
            return
        if "priority" in extra:
            await _answer_with_markdown(message, "priority 参数已取消，请直接使用 /task_new 标题 | type=需求")
            return
        status = _normalize_status(extra.get("status")) or TASK_STATUSES[0]
        task_type = _normalize_task_type(extra.get("type"))
        if task_type is None:
            await _answer_with_markdown(
                message,
                "任务类型缺失或无效，请使用 type=需求/缺陷/优化/风险",
            )
            return
        description = extra.get("description")
        actor = _actor_from_message(message)
        task = await TASK_SERVICE.create_root_task(
            title=title,
            status=status,
            priority=DEFAULT_PRIORITY,
            task_type=task_type,
            tags=(),
            due_date=None,
            description=description,
            actor=actor,
        )
        detail_text, markup = await _render_task_detail(task.id)
        await _answer_with_markdown(message, f"任务已创建：\n{detail_text}", reply_markup=markup)
        return

    await state.clear()
    await state.update_data(
        actor=_actor_from_message(message),
        priority=DEFAULT_PRIORITY,
    )
    await state.set_state(TaskCreateStates.waiting_title)
    await message.answer("请输入任务标题：")


@router.message(TaskCreateStates.waiting_title)
async def on_task_create_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("标题不能为空，请重新输入：")
        return
    await state.update_data(title=title)
    await state.set_state(TaskCreateStates.waiting_type)
    await message.answer(
        "请选择任务类型（需求 / 缺陷 / 优化 / 风险）：",
        reply_markup=_build_task_type_keyboard(),
    )


@router.message(TaskCreateStates.waiting_type)
async def on_task_create_type(message: Message, state: FSMContext) -> None:
    options = [_format_task_type(task_type) for task_type in TASK_TYPES]
    options.append("取消")
    resolved = _resolve_reply_choice(message.text, options=options)
    candidate = resolved or (message.text or "").strip()
    if resolved == "取消" or candidate == "取消":
        await state.clear()
        await message.answer("已取消创建任务。", reply_markup=_build_worker_main_keyboard())
        return
    task_type = _normalize_task_type(candidate)
    if task_type is None:
        await message.answer(
            "任务类型无效，请从键盘选择或输入需求/缺陷/优化/风险：",
            reply_markup=_build_task_type_keyboard(),
        )
        return
    await state.update_data(task_type=task_type)
    await state.set_state(TaskCreateStates.waiting_description)
    await message.answer(
        (
            "请输入任务描述，建议说明业务背景与预期结果。\n"
            "若暂时没有可点击“跳过”按钮或直接发送空消息，发送“取消”可终止。"
        ),
        reply_markup=_build_description_keyboard(),
    )


@router.message(TaskCreateStates.waiting_description)
async def on_task_create_description(message: Message, state: FSMContext) -> None:
    raw_text = message.text or ""
    trimmed = raw_text.strip()
    options = [SKIP_TEXT, "取消"]
    resolved = _resolve_reply_choice(raw_text, options=options)
    if resolved == "取消":
        await state.clear()
        await message.answer("已取消创建任务。", reply_markup=_build_worker_main_keyboard())
        return
    if trimmed and resolved != SKIP_TEXT and len(trimmed) > DESCRIPTION_MAX_LENGTH:
        await message.answer(
            f"任务描述长度不可超过 {DESCRIPTION_MAX_LENGTH} 字，请重新输入：",
            reply_markup=_build_description_keyboard(),
        )
        return
    description: str = ""
    if trimmed and resolved != SKIP_TEXT:
        description = raw_text.strip()
    await state.update_data(description=description)
    await state.set_state(TaskCreateStates.waiting_confirm)
    data = await state.get_data()
    task_type_code = data.get("task_type")
    summary_lines = [
        "请确认任务信息：",
        f"标题：{data.get('title')}",
        f"类型：{_format_task_type(task_type_code)}",
    ]
    priority_text = _format_priority(int(data.get("priority", DEFAULT_PRIORITY)))
    summary_lines.append(f"优先级：{priority_text}（默认）")
    if description:
        summary_lines.append("描述：")
        summary_lines.append(description)
    else:
        summary_lines.append("描述：暂无（可稍后通过 /task_desc 补充）")
    await message.answer("\n".join(summary_lines), reply_markup=_build_worker_main_keyboard())
    await message.answer("是否创建该任务？", reply_markup=_build_confirm_keyboard())


@router.message(TaskCreateStates.waiting_confirm)
async def on_task_create_confirm(message: Message, state: FSMContext) -> None:
    options = ["✅ 确认创建", "❌ 取消"]
    resolved = _resolve_reply_choice(message.text, options=options)
    stripped = _strip_number_prefix((message.text or "").strip()).lower()
    if resolved == options[1] or stripped in {"取消"}:
        await state.clear()
        await message.answer("已取消创建任务。", reply_markup=ReplyKeyboardRemove())
        await message.answer("已返回主菜单。", reply_markup=_build_worker_main_keyboard())
        return
    if resolved != options[0] and stripped not in {"确认", "确认创建"}:
        await message.answer(
            "请选择“确认创建”或“取消”，可直接输入编号或点击键盘按钮：",
            reply_markup=_build_confirm_keyboard(),
        )
        return
    data = await state.get_data()
    title = data.get("title")
    if not title:
        await state.clear()
        await message.answer(
            "创建数据缺失，请重新执行 /task_new。",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer("会话已返回主菜单。", reply_markup=_build_worker_main_keyboard())
        return
    priority_raw = data.get("priority")
    if not isinstance(priority_raw, int):
        parent_priority_value = data.get("parent_priority", DEFAULT_PRIORITY)
        priority_raw = parent_priority_value if isinstance(parent_priority_value, int) else DEFAULT_PRIORITY
    priority = int(priority_raw)
    task_type = data.get("task_type")
    if task_type is None:
        await state.clear()
        await message.answer(
            "任务类型缺失，请重新执行 /task_new。",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer("会话已返回主菜单。", reply_markup=_build_worker_main_keyboard())
        return
    actor = data.get("actor") or _actor_from_message(message)
    task = await TASK_SERVICE.create_root_task(
        title=title,
        status=TASK_STATUSES[0],
        priority=priority,
        task_type=task_type,
        tags=(),
        due_date=None,
        description=data.get("description"),
        actor=actor,
    )
    await state.clear()
    detail_text, markup = await _render_task_detail(task.id)
    await message.answer("任务已创建。", reply_markup=_build_worker_main_keyboard())
    await _answer_with_markdown(message, f"任务已创建：\n{detail_text}", reply_markup=markup)


@router.message(Command("task_child"))
async def on_task_child(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _answer_with_markdown(
        message,
        "子任务功能已下线，历史子任务已自动归档。请使用 /task_new 创建新的任务。",
    )


@router.callback_query(
    F.data.in_(
        {
            "task:create_confirm",
            "task:create_cancel",
            "task:child_confirm",
            "task:child_cancel",
        }
    )
)
async def on_outdated_confirm_callback(callback: CallbackQuery) -> None:
    await callback.answer("子任务功能已下线，相关按钮已失效，请使用 /task_new 创建任务。", show_alert=True)


@router.callback_query(F.data.startswith("task:desc_edit:"))
async def on_task_desc_edit(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    origin_message = callback.message
    if origin_message is None:
        await callback.answer("消息已不存在，请重新开始编辑。", show_alert=True)
        return
    await callback.answer()
    await _begin_task_desc_edit_flow(
        state=state,
        task=task,
        actor=_actor_from_message(origin_message),
        origin_message=origin_message,
    )


@router.message(TaskDescriptionStates.waiting_content)
async def on_task_desc_input(message: Message, state: FSMContext) -> None:
    """处理任务描述输入阶段的文本或菜单指令。"""

    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("会话已失效，请重新操作。", reply_markup=_build_worker_main_keyboard())
        return

    token = _normalize_choice_token(message.text or "")
    if _is_cancel_message(token):
        await state.clear()
        await message.answer("已取消编辑任务描述。", reply_markup=_build_worker_main_keyboard())
        return

    if token == _normalize_choice_token(TASK_DESC_CLEAR_TEXT):
        await state.update_data(
            new_description="",
            actor=_actor_from_message(message),
        )
        await state.set_state(TaskDescriptionStates.waiting_confirm)
        await _answer_with_markdown(
            message,
            _build_task_desc_confirm_text("（新描述为空，将清空任务描述）"),
            reply_markup=_build_task_desc_confirm_keyboard(),
        )
        return

    if token == _normalize_choice_token(TASK_DESC_REPROMPT_TEXT):
        await _prompt_task_description_input(
            message,
            current_description=data.get("current_description", ""),
        )
        return

    trimmed = (message.text or "").strip()
    if len(trimmed) > DESCRIPTION_MAX_LENGTH:
        await message.answer(
            f"任务描述长度不可超过 {DESCRIPTION_MAX_LENGTH} 字，请重新输入：",
            reply_markup=_build_task_desc_input_keyboard(),
        )
        await _prompt_task_description_input(
            message,
            current_description=data.get("current_description", ""),
        )
        return

    preview_segment = trimmed if trimmed else "（新描述为空，将清空任务描述）"
    await state.update_data(
        new_description=trimmed,
        actor=_actor_from_message(message),
    )
    await state.set_state(TaskDescriptionStates.waiting_confirm)
    await _answer_with_markdown(
        message,
        _build_task_desc_confirm_text(preview_segment),
        reply_markup=_build_task_desc_confirm_keyboard(),
    )


@router.message(TaskDescriptionStates.waiting_confirm)
async def on_task_desc_confirm_stage_text(message: Message, state: FSMContext) -> None:
    """处理任务描述确认阶段的菜单指令。支持按钮点击、数字编号和直接文本输入。"""

    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("会话已失效，请重新操作。", reply_markup=_build_worker_main_keyboard())
        return

    # 使用 _resolve_reply_choice() 智能解析用户输入，支持数字编号、按钮文本和直接文本
    options = [TASK_DESC_CONFIRM_TEXT, TASK_DESC_RETRY_TEXT, TASK_DESC_CANCEL_TEXT]
    resolved = _resolve_reply_choice(message.text, options=options)
    stripped = _strip_number_prefix((message.text or "").strip()).lower()

    # 处理取消操作
    if resolved == options[2] or _is_cancel_message(resolved) or stripped in {"取消"}:
        await state.clear()
        await message.answer("已取消编辑任务描述。", reply_markup=_build_worker_main_keyboard())
        return

    # 处理重新输入操作
    if resolved == options[1] or stripped in {"重新输入"}:
        task = await TASK_SERVICE.get_task(task_id)
        if task is None:
            await state.clear()
            await message.answer("任务不存在，已结束编辑流程。", reply_markup=_build_worker_main_keyboard())
            return
        await state.update_data(
            new_description=None,
            current_description=task.description or "",
        )
        await state.set_state(TaskDescriptionStates.waiting_content)
        await message.answer("已回到描述输入阶段，请重新输入新的任务描述。", reply_markup=_build_task_desc_input_keyboard())
        await _prompt_task_description_input(
            message,
            current_description=task.description or "",
        )
        return

    # 处理确认更新操作
    if resolved == options[0] or stripped in {"确认", "确认更新"}:
        new_description = data.get("new_description")
        if new_description is None:
            await state.set_state(TaskDescriptionStates.waiting_content)
            await message.answer("描述内容已失效，请重新输入。", reply_markup=_build_task_desc_input_keyboard())
            await _prompt_task_description_input(
                message,
                current_description=data.get("current_description", ""),
            )
            return
        actor = data.get("actor") or _actor_from_message(message)
        try:
            updated = await TASK_SERVICE.update_task(
                task_id,
                actor=actor,
                description=new_description,
            )
        except ValueError as exc:
            await state.clear()
            await message.answer(str(exc), reply_markup=_build_worker_main_keyboard())
            return
        await state.clear()
        await message.answer("任务描述已更新，正在刷新任务详情……", reply_markup=_build_worker_main_keyboard())
        detail_text, markup = await _render_task_detail(updated.id)
        await _answer_with_markdown(
            message,
            f"任务描述已更新：\n{detail_text}",
            reply_markup=markup,
        )
        return

    # 无效输入，提示用户
    await message.answer(
        "当前处于确认阶段，请选择确认、重新输入或取消，可直接输入编号或点击键盘按钮：",
        reply_markup=_build_task_desc_confirm_keyboard(),
    )


@router.callback_query(F.data.startswith("task:desc_"))
async def on_task_desc_legacy_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """兼容旧版内联按钮，提示用户改用菜单按钮。"""

    await callback.answer("任务描述编辑的按钮已移动到菜单栏，请使用菜单操作。", show_alert=True)
    current_state = await state.get_state()
    data = await state.get_data()
    if callback.message is None:
        return
    if current_state == TaskDescriptionStates.waiting_content.state:
        await _prompt_task_description_input(
            callback.message,
            current_description=data.get("current_description", ""),
        )
        return
    if current_state == TaskDescriptionStates.waiting_confirm.state:
        preview_segment = data.get("new_description") or "（新描述为空，将清空任务描述）"
        await _answer_with_markdown(
            callback.message,
            _build_task_desc_confirm_text(preview_segment),
            reply_markup=_build_task_desc_confirm_keyboard(),
        )


@router.callback_query(F.data.startswith("task:push_model:"))
async def on_task_push_model(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    if task.status not in MODEL_PUSH_ELIGIBLE_STATUSES:
        await callback.answer("当前状态暂不支持推送到模型", show_alert=True)
        return
    actor = _actor_from_callback(callback)
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    if task.status in MODEL_PUSH_SUPPLEMENT_STATUSES:
        await state.clear()
        await state.update_data(
            task_id=task_id,
            origin_message=callback.message,
            chat_id=chat_id,
            actor=actor,
        )
        await state.set_state(TaskPushStates.waiting_supplement)
        await callback.answer("请补充任务描述，或点击跳过/取消")
        if callback.message:
            await _prompt_model_supplement_input(callback.message)
        return
    await state.clear()
    try:
        success, prompt, session_path = await _push_task_to_model(
            task,
            chat_id=chat_id,
            reply_to=callback.message,
            supplement=None,
            actor=actor,
        )
    except ValueError as exc:
        worker_log.error(
            "推送模板缺失：%s",
            exc,
            extra={"task_id": task_id, "status": task.status},
        )
        await callback.answer("推送失败：缺少模板配置", show_alert=True)
        return
    if not success:
        await callback.answer("推送失败：模型未就绪", show_alert=True)
        return
    await callback.answer("已推送到模型")
    preview_block, preview_parse_mode = _wrap_text_in_code_block(prompt)
    await _reply_to_chat(
        chat_id,
        f"已推送到模型：\n{preview_block}",
        reply_to=callback.message,
        parse_mode=preview_parse_mode,
    )
    if session_path is not None:
        await _send_session_ack(chat_id, session_path, reply_to=callback.message)


@router.callback_query(F.data.startswith("task:push_model_skip:"))
async def on_task_push_model_skip(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    data = await state.get_data()
    stored_id = data.get("task_id")
    if stored_id and stored_id != task_id:
        task_id = stored_id
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await state.clear()
        await callback.answer("任务不存在", show_alert=True)
        return
    actor = _actor_from_callback(callback)
    chat_id = data.get("chat_id") or (callback.message.chat.id if callback.message else callback.from_user.id)
    origin_message = data.get("origin_message") or callback.message
    try:
        success, prompt, session_path = await _push_task_to_model(
            task,
            chat_id=chat_id,
            reply_to=origin_message,
            supplement=None,
            actor=actor,
        )
    except ValueError as exc:
        await state.clear()
        worker_log.error(
            "推送模板缺失：%s",
            exc,
            extra={"task_id": task_id, "status": task.status},
        )
        await callback.answer("推送失败：缺少模板配置", show_alert=True)
        return
    await state.clear()
    if not success:
        await callback.answer("推送失败：模型未就绪", show_alert=True)
        return
    await callback.answer("已推送到模型")
    preview_block, preview_parse_mode = _wrap_text_in_code_block(prompt)
    await _reply_to_chat(
        chat_id,
        f"已推送到模型：\n{preview_block}",
        reply_to=origin_message,
        parse_mode=preview_parse_mode,
    )
    if session_path is not None:
        await _send_session_ack(chat_id, session_path, reply_to=origin_message)


@router.callback_query(F.data.startswith("task:push_model_fill:"))
async def on_task_push_model_fill(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await state.clear()
        await callback.answer("任务不存在", show_alert=True)
        return
    actor = _actor_from_callback(callback)
    await state.update_data(
        task_id=task_id,
        origin_message=callback.message,
        chat_id=callback.message.chat.id if callback.message else callback.from_user.id,
        actor=actor,
    )
    await state.set_state(TaskPushStates.waiting_supplement)
    await callback.answer()
    if callback.message:
        await _prompt_model_supplement_input(callback.message)


@router.message(TaskPushStates.waiting_supplement)
async def on_task_push_model_supplement(message: Message, state: FSMContext) -> None:
    raw_text = message.text or ""
    trimmed = raw_text.strip()
    options = [SKIP_TEXT, "取消"]
    resolved = _resolve_reply_choice(raw_text, options=options)
    if resolved == "取消" or trimmed == "取消":
        await state.clear()
        await message.answer("已取消推送到模型。", reply_markup=_build_worker_main_keyboard())
        return
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("推送会话已失效，请重新点击按钮。", reply_markup=_build_worker_main_keyboard())
        return
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await state.clear()
        await message.answer("任务不存在，已取消推送。", reply_markup=_build_worker_main_keyboard())
        return
    supplement: Optional[str] = None
    if trimmed and resolved != SKIP_TEXT:
        if len(trimmed) > DESCRIPTION_MAX_LENGTH:
            await message.answer(
                f"补充任务描述长度不可超过 {DESCRIPTION_MAX_LENGTH} 字，请重新输入：",
                reply_markup=_build_description_keyboard(),
            )
            return
        supplement = raw_text.strip()
    chat_id = data.get("chat_id") or message.chat.id
    origin_message = data.get("origin_message")
    actor = data.get("actor") or _actor_from_message(message)
    try:
        success, prompt, session_path = await _push_task_to_model(
            task,
            chat_id=chat_id,
            reply_to=origin_message,
            supplement=supplement,
            actor=actor,
        )
    except ValueError as exc:
        await state.clear()
        worker_log.error(
            "推送模板缺失：%s",
            exc,
            extra={"task_id": task_id, "status": task.status if task else None},
        )
        await message.answer("推送失败：缺少模板配置。", reply_markup=_build_worker_main_keyboard())
        return
    await state.clear()
    if not success:
        await message.answer("推送失败：模型未就绪，请稍后再试。", reply_markup=_build_worker_main_keyboard())
        return
    preview_block, preview_parse_mode = _wrap_text_in_code_block(prompt)
    await _reply_to_chat(
        chat_id,
        f"已推送到模型：\n{preview_block}",
        reply_to=origin_message,
        parse_mode=preview_parse_mode,
        reply_markup=_build_worker_main_keyboard(),
    )
    if session_path is not None:
        await _send_session_ack(chat_id, session_path, reply_to=origin_message)


@router.callback_query(F.data.startswith("task:history:"))
async def on_task_history(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    try:
        text, markup, page, total_pages = await _render_task_history(task_id, page=0)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    history_state = _make_history_view_state(task_id=task_id, page=page)
    code_text, parse_mode = _wrap_text_in_code_block(text)
    try:
        sent = await message.answer(
            code_text,
            parse_mode=parse_mode,
            reply_markup=markup,
        )
    except TelegramBadRequest as exc:
        worker_log.warning(
            "任务事件历史发送失败：%s",
            exc,
            extra={"task_id": task_id},
        )
        await callback.answer("历史记录发送失败", show_alert=True)
        return
    _init_task_view_context(sent, history_state)
    await callback.answer("已展示历史记录")
    worker_log.info(
        "任务事件历史已通过代码块消息展示",
        extra={
            "task_id": task_id,
            "page": str(page),
            "pages": str(total_pages),
        },
    )


@router.callback_query(F.data.startswith(f"{TASK_HISTORY_PAGE_CALLBACK}:"))
async def on_task_history_page(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id, page_raw = parts
    try:
        requested_page = int(page_raw)
    except ValueError:
        await callback.answer("页码无效", show_alert=True)
        return
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    try:
        text, markup, page, total_pages = await _render_task_history(task_id, requested_page)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    history_state = _make_history_view_state(task_id=task_id, page=page)
    code_text, parse_mode = _wrap_text_in_code_block(text)
    try:
        sent = await message.answer(
            code_text,
            parse_mode=parse_mode,
            reply_markup=markup,
        )
    except TelegramBadRequest as exc:
        worker_log.info(
            "历史分页发送失败：%s",
            exc,
            extra={"task_id": task_id, "page": requested_page},
        )
        await callback.answer("切换失败，请稍后重试", show_alert=True)
        return
    chat = getattr(message, "chat", None)
    if chat is not None:
        _clear_task_view(chat.id, message.message_id)
    _init_task_view_context(sent, history_state)
    await callback.answer(f"已展示第 {page}/{total_pages} 页")


@router.callback_query(F.data.startswith(f"{TASK_HISTORY_BACK_CALLBACK}:"))
async def on_task_history_back(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    try:
        text, markup = await _render_task_detail(task_id)
    except ValueError:
        await callback.answer("任务不存在", show_alert=True)
        return
    detail_state = TaskViewState(kind="detail", data={"task_id": task_id})
    chat = getattr(message, "chat", None)
    if chat is not None:
        _clear_task_view(chat.id, message.message_id)
    sent = await _answer_with_markdown(message, text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(sent, detail_state)
        await callback.answer("已返回任务详情")
        return
    await callback.answer("返回失败，请稍后重试", show_alert=True)


class TaskSummaryRequestError(Exception):
    """生成摘要流程中的业务异常。"""


async def _request_task_summary(
    task: TaskRecord,
    *,
    actor: Optional[str],
    chat_id: int,
    reply_to: Optional[Message],
) -> tuple[str, bool]:
    """触发摘要请求，必要时自动调整任务状态。"""

    status_changed = False
    current_task = task
    if current_task.status != "test":
        try:
            updated = await TASK_SERVICE.update_task(
                current_task.id,
                actor=actor,
                status="test",
            )
        except ValueError as exc:
            raise TaskSummaryRequestError(f"任务状态更新失败：{exc}") from exc
        else:
            current_task = updated
            status_changed = True

    history_text, history_count = await _build_history_context_for_model(current_task.id)
    notes = await TASK_SERVICE.list_notes(current_task.id)
    request_id = uuid.uuid4().hex
    prompt = _build_summary_prompt(
        current_task,
        request_id=request_id,
        history_text=history_text,
        notes=notes,
    )

    success, session_path = await _dispatch_prompt_to_model(
        chat_id,
        prompt,
        reply_to=reply_to,
        ack_immediately=False,
    )
    if not success:
        raise TaskSummaryRequestError("模型未就绪，摘要生成失败")

    actor_label = actor
    if session_path is not None:
        session_key = str(session_path)
        PENDING_SUMMARIES[session_key] = PendingSummary(
            task_id=current_task.id,
            request_id=request_id,
            actor=actor_label,
            session_key=session_key,
            session_path=session_path,
            created_at=time.monotonic(),
        )

    payload: dict[str, Any] = {
        "request_id": request_id,
        "model": ACTIVE_MODEL or "",
        "status_auto_updated": status_changed,
    }
    if history_count:
        payload["history_items"] = history_count

    await _log_task_action(
        current_task.id,
        action="summary_request",
        actor=actor_label,
        new_value=request_id,
        payload=payload,
    )

    return request_id, status_changed


@router.message(Command("task_note"))
async def on_task_note(message: Message, state: FSMContext) -> None:
    args = _extract_command_args(message.text)
    if args:
        body, extra = parse_structured_text(args)
        parts = body.split(" ", 1)
        task_id = parts[0].strip() if parts and parts[0].strip() else extra.get("id")
        if not task_id:
            await _answer_with_markdown(message, "请提供任务 ID，例如：/task_note TASK_0001 内容")
            return
        normalized_task_id = _normalize_task_id(task_id)
        if not normalized_task_id:
            await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
            return
        content = parts[1].strip() if len(parts) > 1 else extra.get("content", "").strip()
        if not content:
            await _answer_with_markdown(message, "备注内容不能为空")
            return
        note_type_raw = extra.get("type", "").strip().lower()
        note_type = note_type_raw if note_type_raw in NOTE_TYPES else "misc"
        await TASK_SERVICE.add_note(
            normalized_task_id,
            note_type=note_type,
            content=content,
            actor=_actor_from_message(message),
        )
        detail_text, markup = await _render_task_detail(normalized_task_id)
        await _answer_with_markdown(message, f"备注已添加：\n{detail_text}", reply_markup=markup)
        return

    await state.clear()
    await state.set_state(TaskNoteStates.waiting_task_id)
    await message.answer("请输入任务 ID：")


@router.message(TaskNoteStates.waiting_task_id)
async def on_note_task_id(message: Message, state: FSMContext) -> None:
    task_id_raw = (message.text or "").strip()
    if not task_id_raw:
        await message.answer("任务 ID 不能为空，请重新输入：")
        return
    task_id = _normalize_task_id(task_id_raw)
    if not task_id:
        await message.answer(TASK_ID_USAGE_TIP)
        return
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await message.answer("任务不存在，请重新输入有效的 ID：")
        return
    await state.update_data(task_id=task_id)
    await state.set_state(TaskNoteStates.waiting_content)
    await message.answer("请输入备注内容：")


@router.message(TaskNoteStates.waiting_content)
async def on_note_content(message: Message, state: FSMContext) -> None:
    content = (message.text or "").strip()
    if not content:
        await message.answer("备注内容不能为空，请重新输入：")
        return
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("数据缺失，备注添加失败，请重新执行 /task_note")
        return
    await TASK_SERVICE.add_note(
        task_id,
        note_type="misc",
        content=content,
        actor=_actor_from_message(message),
    )
    await state.clear()
    detail_text, markup = await _render_task_detail(task_id)
    await _answer_with_markdown(message, f"备注已添加：\n{detail_text}", reply_markup=markup)


@router.message(Command("task_update"))
async def on_task_update(message: Message) -> None:
    args = _extract_command_args(message.text)
    if not args:
        await _answer_with_markdown(
            message,
            "用法：/task_update TASK_0001 status=test | priority=2 | description=调研内容",
        )
        return
    body, extra = parse_structured_text(args)
    parts = body.split(" ", 1)
    task_id = parts[0].strip() if parts and parts[0].strip() else extra.get("id")
    if not task_id:
        await _answer_with_markdown(message, "请提供任务 ID")
        return
    normalized_task_id = _normalize_task_id(task_id)
    if not normalized_task_id:
        await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
        return
    title = extra.get("title")
    if title is None and len(parts) > 1:
        title = parts[1].strip()
    status = _normalize_status(extra.get("status"))
    priority = None
    if "priority" in extra:
        try:
            priority = int(extra["priority"])
        except ValueError:
            await _answer_with_markdown(message, "优先级需要为数字 1-5")
            return
        priority = max(1, min(priority, 5))
    description = extra.get("description")
    if description is not None and len(description) > DESCRIPTION_MAX_LENGTH:
        await _answer_with_markdown(
            message,
            f"任务描述长度不可超过 {DESCRIPTION_MAX_LENGTH} 字",
        )
        return
    task_type = None
    if "type" in extra:
        task_type = _normalize_task_type(extra.get("type"))
        if task_type is None:
            await _answer_with_markdown(
                message,
                "任务类型无效，请填写 type=需求/缺陷/优化/风险",
            )
            return
    updates = {
        "title": title,
        "status": status,
        "priority": priority,
        "task_type": task_type,
        "description": description,
    }
    if all(value is None for value in updates.values()):
        await _answer_with_markdown(message, "请提供需要更新的字段，例如 status=test")
        return
    actor = _actor_from_message(message)
    try:
        updated = await TASK_SERVICE.update_task(
            normalized_task_id,
            actor=actor,
            title=updates["title"],
            status=updates["status"],
            priority=updates["priority"],
            task_type=updates["task_type"],
            description=updates["description"],
        )
    except ValueError as exc:
        await _answer_with_markdown(message, str(exc))
        return
    detail_text, markup = await _render_task_detail(updated.id)
    await _answer_with_markdown(message, f"任务已更新：\n{detail_text}", reply_markup=markup)


@router.message(Command("task_delete"))
async def on_task_delete(message: Message) -> None:
    args = _extract_command_args(message.text)
    if not args:
        await _answer_with_markdown(message, "用法：/task_delete TASK_0001 [restore=yes]")
        return
    parts = args.split()
    task_id_raw = parts[0].strip()
    task_id = _normalize_task_id(task_id_raw)
    if not task_id:
        await _answer_with_markdown(message, TASK_ID_USAGE_TIP)
        return
    extra = parse_simple_kv(" ".join(parts[1:])) if len(parts) > 1 else {}
    restore = extra.get("restore", "no").strip().lower() in {"yes", "1", "true"}
    try:
        updated = await TASK_SERVICE.update_task(
            task_id,
            actor=_actor_from_message(message),
            archived=not restore,
        )
    except ValueError as exc:
        await _answer_with_markdown(message, str(exc))
        return
    action = "已恢复" if restore else "已归档"
    detail_text, markup = await _render_task_detail(updated.id)
    await _answer_with_markdown(message, f"任务{action}：\n{detail_text}", reply_markup=markup)


@router.callback_query(F.data.startswith("task:status:"))
async def on_status_callback(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id, status_value = parts
    status = _normalize_status(status_value)
    if status is None:
        await callback.answer("无效的状态", show_alert=True)
        return
    try:
        updated = await TASK_SERVICE.update_task(
            task_id,
            actor=_actor_from_message(callback.message),
            status=status,
        )
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    detail_text, markup = await _render_task_detail(updated.id)
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    detail_state = TaskViewState(kind="detail", data={"task_id": updated.id})
    if await _try_edit_message(message, detail_text, reply_markup=markup):
        _set_task_view_context(message, detail_state)
        await callback.answer("状态已更新")
        return
    sent = await _answer_with_markdown(message, detail_text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(sent, detail_state)
        await callback.answer("状态已更新")
        return
    await callback.answer("状态更新但消息刷新失败", show_alert=True)


@router.callback_query(F.data.startswith("task:summary:"))
async def on_task_summary_request(callback: CallbackQuery) -> None:
    """请求模型生成任务摘要。"""

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    actor = _actor_from_callback(callback)
    try:
        _, status_changed = await _request_task_summary(
            task,
            actor=actor,
            chat_id=chat_id,
            reply_to=callback.message,
        )
    except TaskSummaryRequestError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer("已请求模型生成摘要")
    if callback.message:
        lines = ["已向模型发送摘要请求，请等待回复。"]
        if status_changed:
            lines.append("任务状态已自动更新为“测试”。")
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=_build_worker_main_keyboard(),
        )


@router.message(
    F.text.lower().startswith("/task_summary_request_")
    | F.text.lower().startswith("/tasksummaryrequest")
)
async def on_task_summary_command(message: Message) -> None:
    """命令式触发任务摘要生成。"""

    raw_text = (message.text or "").strip()
    if not raw_text:
        await message.answer("请提供任务 ID，例如：/task_summary_request_TASK_0001")
        return
    token = raw_text.split()[0]
    command_part, _, _bot = token.partition("@")
    lowered = command_part.lower()
    prefix = next(
        (alias for alias in SUMMARY_COMMAND_ALIASES if lowered.startswith(alias)),
        None,
    )
    if prefix is None:
        await message.answer("请提供任务 ID，例如：/task_summary_request_TASK_0001")
        return
    task_segment = command_part[len(prefix) :].strip()
    if not task_segment:
        await message.answer("请提供任务 ID，例如：/task_summary_request_TASK_0001")
        return
    normalized_task_id = _normalize_task_id(task_segment)
    if not normalized_task_id:
        await message.answer(TASK_ID_USAGE_TIP)
        return
    task = await TASK_SERVICE.get_task(normalized_task_id)
    if task is None:
        await message.answer("任务不存在", reply_markup=_build_worker_main_keyboard())
        return
    actor = _actor_from_message(message)
    chat_id = message.chat.id
    try:
        _, status_changed = await _request_task_summary(
            task,
            actor=actor,
            chat_id=chat_id,
            reply_to=message,
        )
    except TaskSummaryRequestError as exc:
        await message.answer(str(exc), reply_markup=_build_worker_main_keyboard())
        return
    lines = ["已向模型发送摘要请求，请等待回复。"]
    if status_changed:
        lines.append("任务状态已自动更新为“测试”。")
    await message.answer("\n".join(lines), reply_markup=_build_worker_main_keyboard())


@router.callback_query(F.data.startswith("task:bug_report:"))
async def on_task_bug_report(callback: CallbackQuery, state: FSMContext) -> None:
    """进入缺陷上报流程。"""

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    await state.clear()
    reporter = _actor_from_callback(callback)
    await state.update_data(
        task_id=task.id,
        reporter=reporter,
        description="",
        reproduction="",
        logs="",
    )
    await state.set_state(TaskBugReportStates.waiting_description)
    await callback.answer("请描述缺陷")
    if callback.message:
        await callback.message.answer(
            _build_bug_report_intro(task),
            reply_markup=_build_description_keyboard(),
        )


@router.message(TaskBugReportStates.waiting_description)
async def on_task_bug_description(message: Message, state: FSMContext) -> None:
    """处理缺陷描述输入。"""

    if _is_cancel_message(message.text):
        await state.clear()
        await message.answer("已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    content = _collect_message_payload(message)
    if not content:
        await message.answer(
            "缺陷描述不能为空，请重新输入：",
            reply_markup=_build_description_keyboard(),
        )
        return
    await state.update_data(
        description=content,
        reporter=_actor_from_message(message),
    )
    await state.set_state(TaskBugReportStates.waiting_reproduction)
    await message.answer(_build_bug_repro_prompt(), reply_markup=_build_description_keyboard())


@router.message(TaskBugReportStates.waiting_reproduction)
async def on_task_bug_reproduction(message: Message, state: FSMContext) -> None:
    """处理复现步骤输入。"""

    if _is_cancel_message(message.text):
        await state.clear()
        await message.answer("已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    options = [SKIP_TEXT, "取消"]
    resolved = _resolve_reply_choice(message.text or "", options=options)
    reproduction = ""
    if resolved not in {SKIP_TEXT, "取消"}:
        reproduction = _collect_message_payload(message)
    await state.update_data(reproduction=reproduction)
    await state.set_state(TaskBugReportStates.waiting_logs)
    await message.answer(_build_bug_log_prompt(), reply_markup=_build_description_keyboard())


@router.message(TaskBugReportStates.waiting_logs)
async def on_task_bug_logs(message: Message, state: FSMContext) -> None:
    """处理日志信息输入。"""

    if _is_cancel_message(message.text):
        await state.clear()
        await message.answer("已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    options = [SKIP_TEXT, "取消"]
    resolved = _resolve_reply_choice(message.text or "", options=options)
    logs = ""
    if resolved not in {SKIP_TEXT, "取消"}:
        logs = _collect_message_payload(message)
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("任务信息缺失，流程已终止。", reply_markup=_build_worker_main_keyboard())
        return
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await state.clear()
        await message.answer("任务不存在，已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    description = data.get("description", "")
    reproduction = data.get("reproduction", "")
    reporter = data.get("reporter") or _actor_from_message(message)
    await state.update_data(logs=logs)
    preview = _build_bug_preview_text(
        task=task,
        description=description,
        reproduction=reproduction,
        logs=logs,
        reporter=reporter,
    )
    await state.set_state(TaskBugReportStates.waiting_confirm)
    await message.answer(
        f"请确认以下缺陷信息：\n{preview}",
        reply_markup=_build_bug_confirm_keyboard(),
    )


@router.message(TaskBugReportStates.waiting_confirm)
async def on_task_bug_confirm(message: Message, state: FSMContext) -> None:
    """确认并写入缺陷记录。"""

    if _is_cancel_message(message.text):
        await state.clear()
        await message.answer("已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    resolved = _resolve_reply_choice(message.text or "", options=["✅ 确认提交", "❌ 取消"])
    if resolved == "❌ 取消":
        await state.clear()
        await message.answer("已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    if resolved not in {"✅ 确认提交"}:
        await message.answer("请回复“✅ 确认提交”或输入“取消”。", reply_markup=_build_bug_confirm_keyboard())
        return
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        await state.clear()
        await message.answer("任务信息缺失，流程已终止。", reply_markup=_build_worker_main_keyboard())
        return
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await state.clear()
        await message.answer("任务不存在，已取消缺陷上报。", reply_markup=_build_worker_main_keyboard())
        return
    description = data.get("description", "")
    reproduction = data.get("reproduction", "")
    logs = data.get("logs", "")
    reporter = data.get("reporter") or _actor_from_message(message)
    payload = {
        "action": "bug_report",
        "description_length": len(description),
        "has_reproduction": bool(reproduction.strip()),
        "has_logs": bool(logs.strip()),
        "description": description,
        "reproduction": reproduction,
        "logs": logs,
        "reporter": reporter,
    }
    await _log_task_action(
        task.id,
        action="bug_report",
        actor=reporter,
        new_value=description[:HISTORY_DISPLAY_VALUE_LIMIT],
        payload=payload,
    )
    await state.clear()
    await _auto_push_after_bug_report(task, message=message, actor=reporter)


@router.callback_query(F.data.startswith("task:add_note:"))
async def on_add_note_callback(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    await state.clear()
    await state.update_data(task_id=task_id)
    await state.set_state(TaskNoteStates.waiting_content)
    await callback.answer("请输入备注内容")
    await callback.message.answer("请输入备注内容：")


@router.callback_query(F.data.startswith("task:add_child:"))
async def on_add_child_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("子任务功能已下线", show_alert=True)
    if callback.message:
        await callback.message.answer(
            "子任务功能已下线，历史子任务已自动归档。请使用 /task_new 创建新的任务。",
            reply_markup=_build_worker_main_keyboard(),
        )


@router.callback_query(F.data.startswith("task:list_children:"))
async def on_list_children_callback(callback: CallbackQuery) -> None:
    await callback.answer("子任务功能已下线", show_alert=True)
    if callback.message:
        await callback.message.answer(
            "子任务功能已下线，历史子任务已自动归档。请使用 /task_new 创建新的任务。",
            reply_markup=_build_worker_main_keyboard(),
        )


@router.callback_query(F.data.startswith("task:detail:"))
async def on_task_detail_callback(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    try:
        detail_text, markup = await _render_task_detail(task_id)
    except ValueError:
        await callback.answer("任务不存在", show_alert=True)
        return
    await callback.answer()
    detail_state = TaskViewState(kind="detail", data={"task_id": task_id})
    chat = getattr(message, "chat", None)
    base_state = _peek_task_view(chat.id, message.message_id) if chat else None
    if base_state is None:
        sent = await _answer_with_markdown(message, detail_text, reply_markup=markup)
        if sent is not None:
            _init_task_view_context(sent, detail_state)
        else:
            # 修复：消息发送失败时给用户反馈
            await message.answer(
                f"⚠️ 任务详情显示失败，可能包含特殊字符。\n任务ID: {task_id}\n请联系管理员检查任务内容。"
            )
        return
    if await _try_edit_message(message, detail_text, reply_markup=markup):
        _push_detail_view(message, task_id)
        return
    sent = await _answer_with_markdown(message, detail_text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(sent, detail_state)
    else:
        # 修复：消息发送失败时给用户反馈
        await message.answer(
            f"⚠️ 任务详情显示失败，可能包含特殊字符。\n任务ID: {task_id}\n请联系管理员检查任务内容。"
        )


async def _fallback_task_detail_back(callback: CallbackQuery) -> None:
    """当视图栈缺失时，回退到旧的 /task_list 触发方式。"""

    message = callback.message
    user = callback.from_user
    if message is None or user is None:
        await callback.answer("无法定位会话", show_alert=True)
        return
    await callback.answer()
    bot = current_bot()
    command_text = "/task_list"
    try:
        now = datetime.now(tz=ZoneInfo("UTC"))
    except ZoneInfoNotFoundError:
        now = datetime.now(UTC)
    entities = [
        MessageEntity(type="bot_command", offset=0, length=len(command_text)),
    ]
    synthetic_message = message.model_copy(
        update={
            "message_id": message.message_id + 1,
            "date": now,
            "edit_date": None,
            "text": command_text,
            "from_user": user,
            "entities": entities,
        }
    )
    update = Update.model_construct(
        update_id=int(time.time() * 1000),
        message=synthetic_message,
    )
    await dp.feed_update(bot, update)


@router.callback_query(F.data == TASK_DETAIL_BACK_CALLBACK)
async def on_task_detail_back(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        await callback.answer("无法定位会话", show_alert=True)
        return
    popped = _pop_detail_view(message)
    if popped is None:
        await _fallback_task_detail_back(callback)
        return
    chat = getattr(message, "chat", None)
    if chat is None:
        await _fallback_task_detail_back(callback)
        return
    prev_state = _peek_task_view(chat.id, message.message_id)
    if prev_state is None:
        await _fallback_task_detail_back(callback)
        return
    try:
        text, markup = await _render_task_view_from_state(prev_state)
    except Exception as exc:  # pragma: no cover - 极端情况下进入兜底
        worker_log.warning(
            "恢复任务视图失败：%s",
            exc,
            extra={"chat": message.chat.id, "message": message.message_id},
        )
        await _fallback_task_detail_back(callback)
        return
    if await _try_edit_message(message, text, reply_markup=markup):
        await callback.answer("已返回任务列表")
        return
    _clear_task_view(chat.id, message.message_id)
    sent = await _answer_with_markdown(message, text, reply_markup=markup)
    if sent is not None:
        cloned_state = TaskViewState(kind=prev_state.kind, data=dict(prev_state.data))
        _init_task_view_context(sent, cloned_state)
        await callback.answer("已返回任务列表")
        return
    await _fallback_task_detail_back(callback)


@router.callback_query(F.data.startswith("task:toggle_archive:"))
async def on_toggle_archive(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    updated = await TASK_SERVICE.update_task(
        task_id,
        actor=_actor_from_message(callback.message),
        archived=not task.archived,
    )
    detail_text, markup = await _render_task_detail(updated.id)
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    detail_state = TaskViewState(kind="detail", data={"task_id": updated.id})
    if await _try_edit_message(message, detail_text, reply_markup=markup):
        _set_task_view_context(message, detail_state)
        await callback.answer("已切换任务状态")
        return
    sent = await _answer_with_markdown(message, detail_text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(sent, detail_state)
        await callback.answer("已切换任务状态")
        return
    await callback.answer("状态已切换但消息刷新失败", show_alert=True)


@router.callback_query(F.data.startswith("task:refresh:"))
async def on_refresh_callback(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    message = callback.message
    if message is None:
        await callback.answer("无法定位原消息", show_alert=True)
        return
    try:
        detail_text, markup = await _render_task_detail(task_id)
    except ValueError:
        await callback.answer("任务不存在", show_alert=True)
        return
    detail_state = TaskViewState(kind="detail", data={"task_id": task_id})
    if await _try_edit_message(message, detail_text, reply_markup=markup):
        _set_task_view_context(message, detail_state)
        await callback.answer("已刷新")
        return
    sent = await _answer_with_markdown(message, detail_text, reply_markup=markup)
    if sent is not None:
        _init_task_view_context(sent, detail_state)
        await callback.answer("已刷新")
        return
    await callback.answer("刷新失败", show_alert=True)


@router.callback_query(F.data.startswith("task:edit:"))
async def on_edit_callback(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("回调参数错误", show_alert=True)
        return
    _, _, task_id = parts
    task = await TASK_SERVICE.get_task(task_id)
    if task is None:
        await callback.answer("任务不存在", show_alert=True)
        return
    await state.clear()
    await state.update_data(task_id=task_id, actor=_actor_from_message(callback.message))
    await state.set_state(TaskEditStates.waiting_field_choice)
    await callback.answer("请选择需要编辑的字段")
    await callback.message.answer("请选择需要修改的字段：", reply_markup=_build_edit_field_keyboard())


@router.message(TaskEditStates.waiting_field_choice)
async def on_edit_field_choice(message: Message, state: FSMContext) -> None:
    options = ["标题", "优先级", "类型", "描述", "状态", "取消"]
    resolved = _resolve_reply_choice(message.text, options=options)
    choice = resolved or (message.text or "").strip()
    mapping = {
        "标题": "title",
        "优先级": "priority",
        "类型": "task_type",
        "描述": "description",
    }
    if choice == "取消":
        await state.clear()
        await message.answer("已取消编辑", reply_markup=_build_worker_main_keyboard())
        return
    field = mapping.get(choice)
    if choice == "状态":
        await state.clear()
        await message.answer("请使用任务详情中的状态按钮进行切换。", reply_markup=_build_worker_main_keyboard())
        return
    if field is None:
        await message.answer("暂不支持该字段，请重新选择：", reply_markup=_build_edit_field_keyboard())
        return
    if field == "description":
        data = await state.get_data()
        task_id = data.get("task_id")
        if not task_id:
            await state.clear()
            await message.answer("任务信息缺失，已取消编辑。", reply_markup=_build_worker_main_keyboard())
            return
        task = await TASK_SERVICE.get_task(task_id)
        if task is None:
            await state.clear()
            await message.answer("任务不存在，已取消编辑。", reply_markup=_build_worker_main_keyboard())
            return
        actor = data.get("actor") or _actor_from_message(message)
        await _begin_task_desc_edit_flow(
            state=state,
            task=task,
            actor=actor,
            origin_message=message,
        )
        return
    await state.update_data(field=field)
    await state.set_state(TaskEditStates.waiting_new_value)
    if field == "priority":
        await message.answer("请输入新的优先级（1-5）：", reply_markup=_build_priority_keyboard())
    elif field == "task_type":
        await message.answer(
            "请选择新的任务类型（需求 / 缺陷 / 优化 / 风险）：",
            reply_markup=_build_task_type_keyboard(),
        )
    else:
        await message.answer("请输入新的值：", reply_markup=_build_worker_main_keyboard())


@router.message(TaskEditStates.waiting_new_value)
async def on_edit_new_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_id = data.get("task_id")
    field = data.get("field")
    if not task_id or not field:
        await state.clear()
        await message.answer("数据缺失，已取消编辑。", reply_markup=_build_worker_main_keyboard())
        return
    raw_text = message.text or ""
    text = raw_text.strip()
    resolved_task_type: Optional[str] = None
    if field == "task_type":
        task_type_options = [_format_task_type(task_type) for task_type in TASK_TYPES]
        task_type_options.append("取消")
        resolved_task_type = _resolve_reply_choice(raw_text, options=task_type_options)
        if resolved_task_type == "取消":
            await state.clear()
            await message.answer("已取消编辑", reply_markup=_build_worker_main_keyboard())
            return
    elif text == "取消":
        await state.clear()
        await message.answer("已取消编辑", reply_markup=_build_worker_main_keyboard())
        return

    update_kwargs: dict[str, Any] = {}
    if field == "priority":
        priority_options = [str(i) for i in range(1, 6)]
        priority_options.append(SKIP_TEXT)
        resolved_priority = _resolve_reply_choice(raw_text, options=priority_options)
        if resolved_priority == SKIP_TEXT:
            await message.answer("优先级请输入 1-5 的数字：", reply_markup=_build_priority_keyboard())
            return
        candidate = resolved_priority or text
        try:
            value = int(candidate)
        except ValueError:
            await message.answer("优先级请输入 1-5 的数字：", reply_markup=_build_priority_keyboard())
            return
        value = max(1, min(value, 5))
        update_kwargs["priority"] = value
    elif field == "description":
        if len(text) > DESCRIPTION_MAX_LENGTH:
            await message.answer(
                f"任务描述长度不可超过 {DESCRIPTION_MAX_LENGTH} 字，请重新输入：",
                reply_markup=_build_worker_main_keyboard(),
            )
            return
        update_kwargs["description"] = text
    elif field == "task_type":
        candidate = resolved_task_type or text
        task_type = _normalize_task_type(candidate)
        if task_type is None:
            await message.answer(
                "任务类型无效，请重新输入需求/缺陷/优化/风险：",
                reply_markup=_build_task_type_keyboard(),
            )
            return
        update_kwargs["task_type"] = task_type
    else:
        if not text:
            await message.answer("标题不能为空，请重新输入：", reply_markup=_build_worker_main_keyboard())
            return
        update_kwargs["title"] = text
    await state.clear()
    try:
        updated = await TASK_SERVICE.update_task(
            task_id,
            actor=_actor_from_message(message),
            title=update_kwargs.get("title"),
            priority=update_kwargs.get("priority"),
            task_type=update_kwargs.get("task_type"),
            description=update_kwargs.get("description"),
        )
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=_build_worker_main_keyboard())
        return
    detail_text, markup = await _render_task_detail(updated.id)
    await _answer_with_markdown(message, f"任务已更新：\n{detail_text}", reply_markup=markup)


@router.message(CommandStart())
async def on_start(m: Message):
    # 首次收到消息时自动记录 chat_id 到 state 文件
    _auto_record_chat_id(m.chat.id)

    await m.answer(
        (
            f"Hello, {m.from_user.full_name}！\n"
            "直接发送问题就能与模型对话，\n"
            "或使用任务功能来组织需求与执行记录。\n\n"
            "主菜单已准备好，祝你使用愉快！"
        ),
        reply_markup=_build_worker_main_keyboard(),
    )
    worker_log.info("收到 /start，chat_id=%s", m.chat.id, extra=_session_extra())
    if ENV_ISSUES:
        await m.answer(_format_env_issue_message())

@router.message(F.text)
async def on_text(m: Message):
    # 首次收到消息时自动记录 chat_id 到 state 文件
    _auto_record_chat_id(m.chat.id)

    prompt = (m.text or "").strip()
    if not prompt:
        return await m.answer("请输入非空提示词")
    task_id_candidate = _normalize_task_id(prompt)
    if task_id_candidate:
        await _reply_task_detail_message(m, task_id_candidate)
        return
    if prompt.startswith("/"):
        return

    if ENV_ISSUES:
        message = _format_env_issue_message()
        worker_log.warning(
            "拒绝处理消息，环境异常: %s",
            message,
            extra={**_session_extra(), "chat": m.chat.id},
        )
        await m.answer(message)
        return

    bot = current_bot()
    await bot.send_chat_action(m.chat.id, "typing")  # “正在输入”提示

    if MODE == "A":
        if not AGENT_CMD:
            return await m.answer("AGENT_CMD 未配置（.env）")
        rc, out = run_subprocess_capture(AGENT_CMD, input_text=prompt)
        out = out or ""
        out = out + ("" if rc == 0 else f"\n(exit={rc})")
        await reply_large_text(m.chat.id, out)

    else:
        await _dispatch_prompt_to_model(m.chat.id, prompt, reply_to=m)


async def ensure_telegram_connectivity(bot: Bot, timeout: float = 30.0):
    """启动前校验 Telegram 连通性，便于快速定位代理/网络问题"""
    try:
        if hasattr(asyncio, "timeout"):
            async with asyncio.timeout(timeout):
                me = await bot.get_me()
        else:
            me = await asyncio.wait_for(bot.get_me(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise RuntimeError(f"在 {timeout} 秒内未能与 Telegram 成功握手") from exc
    except TelegramNetworkError as exc:
        raise RuntimeError("Telegram 网络请求失败，请检查代理或网络策略") from exc
    except ClientError as exc:
        raise RuntimeError("无法连接到代理或 Telegram，请检查代理配置") from exc
    else:
        worker_log.info(
            "Telegram 连接正常，Bot=%s (id=%s)",
            me.username,
            me.id,
            extra=_session_extra(),
        )
        return me


async def _ensure_bot_commands(bot: Bot) -> None:
    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in BOT_COMMANDS]
    scopes: list[tuple[Optional[object], str]] = [
        (None, "default"),
        (BotCommandScopeAllPrivateChats(), "all_private"),
        (BotCommandScopeAllGroupChats(), "all_groups"),
        (BotCommandScopeAllChatAdministrators(), "group_admins"),
    ]
    for scope, label in scopes:
        try:
            if scope is None:
                await bot.set_my_commands(commands)
            else:
                await bot.set_my_commands(commands, scope=scope)
        except TelegramBadRequest as exc:
            worker_log.warning(
                "设置 Bot 命令失败：%s",
                exc,
                extra={**_session_extra(), "scope": label},
            )
        else:
            worker_log.info(
                "Bot 命令已同步",
                extra={**_session_extra(), "scope": label},
            )


async def _ensure_worker_menu_button(bot: Bot) -> None:
    """确保 worker 侧聊天菜单按钮文本为任务列表入口。"""
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonCommands(text=WORKER_MENU_BUTTON_TEXT),
        )
    except TelegramBadRequest as exc:
        worker_log.warning(
            "设置聊天菜单失败：%s",
            exc,
            extra=_session_extra(),
        )
    else:
        worker_log.info(
            "聊天菜单已同步",
            extra={**_session_extra(), "text": WORKER_MENU_BUTTON_TEXT},
        )

async def main():
    global _bot, CHAT_LONG_POLL_LOCK
    # 初始化长轮询锁
    CHAT_LONG_POLL_LOCK = asyncio.Lock()
    _bot = build_bot()
    try:
        await ensure_telegram_connectivity(_bot)
    except Exception as exc:
        worker_log.error("Telegram 连通性检查失败：%s", exc, extra=_session_extra())
        if _bot:
            await _bot.session.close()
        raise SystemExit(1)
    try:
        await TASK_SERVICE.initialize()
    except Exception as exc:
        worker_log.error("任务数据库初始化失败：%s", exc, extra=_session_extra())
        if _bot:
            await _bot.session.close()
        raise SystemExit(1)
    await _ensure_bot_commands(_bot)
    await _ensure_worker_menu_button(_bot)
    await _broadcast_worker_keyboard(_bot)

    try:
        await dp.start_polling(_bot)
    finally:
        if _bot:
            await _bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
