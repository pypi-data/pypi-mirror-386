"""Master bot controller.

统一管理多个项目 worker：
- 读取 `config/master.db`（自动同步 `config/projects.json`）获取项目配置
- 维护 `state/state.json`，记录运行状态 / 当前模型 / 自动记录的 chat_id
- 暴露 /projects、/run、/stop、/switch、/authorize 等命令
- 调用 `scripts/run_bot.sh` / `scripts/stop_bot.sh` 控制 worker 进程
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import shutil
import subprocess
import sys
import signal
import shlex
import stat
import textwrap
import re
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from aiogram import Bot, Dispatcher, Router, F
from aiohttp import BasicAuth
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    MenuButtonCommands,
    User,
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
)
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from logging_setup import create_logger
from project_repository import ProjectRepository, ProjectRecord
from tasks.fsm import ProjectDeleteStates

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("MASTER_PROJECTS_PATH", ROOT_DIR / "config/projects.json"))
CONFIG_DB_PATH = Path(os.environ.get("MASTER_PROJECTS_DB_PATH", ROOT_DIR / "config/master.db"))
STATE_PATH = Path(os.environ.get("MASTER_STATE_PATH", ROOT_DIR / "state/state.json"))
RUN_SCRIPT = ROOT_DIR / "scripts/run_bot.sh"
STOP_SCRIPT = ROOT_DIR / "scripts/stop_bot.sh"
RESTART_SIGNAL_PATH = Path(
    os.environ.get("MASTER_RESTART_SIGNAL_PATH", ROOT_DIR / "state/restart_signal.json")
)
RESTART_SIGNAL_TTL = int(os.environ.get("MASTER_RESTART_SIGNAL_TTL", "600"))  # 默认 10 分钟
LOCAL_TZ = ZoneInfo(os.environ.get("MASTER_TIMEZONE", "Asia/Shanghai"))
JUMP_BUTTON_TEXT_WIDTH = 40

_DEFAULT_LOG_ROOT = ROOT_DIR / "logs"
LOG_ROOT_PATH = Path(os.environ.get("LOG_ROOT", str(_DEFAULT_LOG_ROOT))).expanduser()

WORKER_HEALTH_TIMEOUT = float(os.environ.get("WORKER_HEALTH_TIMEOUT", "20"))
WORKER_HEALTH_INTERVAL = float(os.environ.get("WORKER_HEALTH_INTERVAL", "0.5"))
WORKER_HEALTH_LOG_TAIL = int(os.environ.get("WORKER_HEALTH_LOG_TAIL", "80"))
HANDSHAKE_MARKERS = (
    "Telegram 连接正常",
)
DELETE_CONFIRM_TIMEOUT = int(os.environ.get("MASTER_DELETE_CONFIRM_TIMEOUT", "120"))

_ENV_FILE_RAW = os.environ.get("MASTER_ENV_FILE")
MASTER_ENV_FILE = Path(_ENV_FILE_RAW).expanduser() if _ENV_FILE_RAW else None
_ENV_LOCK = threading.Lock()

MASTER_MENU_BUTTON_TEXT = "📂 项目列表"
# 旧版本键盘的文案，用于兼容仍显示英文的客户端消息
MASTER_MENU_BUTTON_LEGACY_TEXTS: Tuple[str, ...] = ("📂 Projects",)
# 允许触发项目列表的全部文案，优先匹配最新文案
MASTER_MENU_BUTTON_ALLOWED_TEXTS: Tuple[str, ...] = (
    MASTER_MENU_BUTTON_TEXT,
    *MASTER_MENU_BUTTON_LEGACY_TEXTS,
)
MASTER_MANAGE_BUTTON_TEXT = "⚙️ 项目管理"
MASTER_MANAGE_BUTTON_ALLOWED_TEXTS: Tuple[str, ...] = (MASTER_MANAGE_BUTTON_TEXT,)
MASTER_BOT_COMMANDS: List[Tuple[str, str]] = [
    ("start", "启动 master 菜单"),
    ("projects", "查看项目列表"),
    ("run", "启动 worker"),
    ("stop", "停止 worker"),
    ("switch", "切换 worker 模型"),
    ("authorize", "登记 chat"),
    ("restart", "重启 master"),
]
MASTER_BROADCAST_MESSAGE = os.environ.get("MASTER_BROADCAST_MESSAGE", "")
SWITCHABLE_MODELS: Tuple[Tuple[str, str], ...] = (
    ("codex", "⚙️ Codex"),
    ("claudecode", "⚙️ ClaudeCode"),
)


def _build_master_main_keyboard() -> ReplyKeyboardMarkup:
    """构造 Master Bot 主键盘，提供项目列表与管理入口。"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MASTER_MENU_BUTTON_TEXT),
                KeyboardButton(text=MASTER_MANAGE_BUTTON_TEXT),
            ]
        ],
        resize_keyboard=True,
    )


async def _ensure_master_menu_button(bot: Bot) -> None:
    """同步 master 端聊天菜单按钮文本，修复旧客户端的缓存问题。"""
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonCommands(text=MASTER_MENU_BUTTON_TEXT),
        )
    except TelegramBadRequest as exc:
        log.warning("设置聊天菜单失败：%s", exc)
    else:
        log.info("聊天菜单已同步", extra={"text": MASTER_MENU_BUTTON_TEXT})


async def _ensure_master_commands(bot: Bot) -> None:
    """同步 master 侧命令列表，确保新增/删除命令立即生效。"""
    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in MASTER_BOT_COMMANDS]
    scopes: List[Tuple[Optional[object], str]] = [
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
            log.warning("设置 master 命令失败：%s", exc, extra={"scope": label})
        else:
            log.info("master 命令已同步", extra={"scope": label})


def _collect_master_broadcast_targets(manager: MasterManager) -> List[int]:
    """汇总需要推送键盘的 chat_id，避免重复广播。"""
    targets: set[int] = set(manager.admin_ids or [])
    manager.refresh_state()
    for state in manager.state_store.data.values():
        if state.chat_id:
            targets.add(state.chat_id)
    return sorted(targets)


async def _broadcast_master_keyboard(bot: Bot, manager: MasterManager) -> None:
    """在 master 启动阶段主动推送菜单键盘，覆盖 Telegram 端缓存。"""
    targets = _collect_master_broadcast_targets(manager)
    # 当广播消息为空时表示不再向管理员推送启动提示，满足“禁止发送 /task_list”需求。
    if not MASTER_BROADCAST_MESSAGE:
        log.info("启动广播已禁用，跳过 master 键盘推送。")
        return
    if not targets:
        log.info("无可推送的 master 聊天对象")
        return
    markup = _build_master_main_keyboard()
    for chat_id in targets:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=MASTER_BROADCAST_MESSAGE,
                reply_markup=markup,
            )
        except TelegramForbiddenError as exc:
            log.warning("推送菜单被禁止：%s", exc, extra={"chat": chat_id})
        except TelegramBadRequest as exc:
            log.warning("推送菜单失败：%s", exc, extra={"chat": chat_id})
        except Exception as exc:
            log.error("推送菜单异常：%s", exc, extra={"chat": chat_id})
        else:
            log.info("已推送菜单至 chat_id=%s", chat_id)


def _ensure_numbered_markup(markup: Optional[InlineKeyboardMarkup]) -> Optional[InlineKeyboardMarkup]:
    """对 InlineKeyboard 保持原始文案，不再自动追加编号。"""
    return markup


def _terminate_other_master_processes(grace: float = 3.0) -> None:
    """在新 master 启动后终止其他残留 master 进程"""
    existing: list[int] = []
    try:
        result = subprocess.run(
            ["pgrep", "-f", "[Pp]ython.*master.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return
    my_pid = os.getpid()
    for line in result.stdout.split():
        try:
            pid = int(line.strip())
        except ValueError:
            continue
        if pid == my_pid:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            existing.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            log.warning("终止残留 master 进程失败: %s", exc, extra={"pid": pid})
    if not existing:
        return
    deadline = time.monotonic() + grace
    alive = set(existing)
    while alive and time.monotonic() < deadline:
        time.sleep(0.2)
        for pid in list(alive):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                alive.discard(pid)
    for pid in alive:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            log.warning("强制终止 master 进程失败: %s", exc, extra={"pid": pid})
    if existing:
        log.info("清理其他 master 进程完成", extra={"terminated": existing, "force": list(alive)})



def load_env(file: str = ".env") -> None:
    """加载默认 .env 以及 MASTER_ENV_FILE 指向的配置。"""

    candidates: List[Path] = []
    if MASTER_ENV_FILE:
        candidates.append(MASTER_ENV_FILE)
    env_path = ROOT_DIR / file
    candidates.append(env_path)
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _collect_admin_targets() -> List[int]:
    """汇总所有潜在管理员 chat_id，避免广播遗漏。"""

    if MANAGER is not None and getattr(MANAGER, "admin_ids", None):
        return sorted(MANAGER.admin_ids)
    env_value = os.environ.get("MASTER_ADMIN_IDS") or os.environ.get("ALLOWED_CHAT_ID", "")
    targets: List[int] = []
    for item in env_value.split(","):
        item = item.strip()
        if not item:
            continue
        if item.isdigit():
            targets.append(int(item))
    chat_env = os.environ.get("MASTER_CHAT_ID", "")
    if chat_env.isdigit():
        targets.append(int(chat_env))
    return sorted(set(targets))


def _kill_existing_tmux(prefix: str) -> None:
    """终止所有匹配前缀的 tmux 会话，避免多实例冲突。"""

    if shutil.which("tmux") is None:
        return
    try:
        result = subprocess.run(
            ["tmux", "-u", "list-sessions"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return
    full_prefix = prefix if prefix.endswith("-") else f"{prefix}-"
    sessions = []
    for line in result.stdout.splitlines():
        name = line.split(":", 1)[0].strip()
        if name.startswith(full_prefix):
            sessions.append(name)
    for name in sessions:
        subprocess.run(["tmux", "-u", "kill-session", "-t", name], check=False)


def _mask_proxy(url: str) -> str:
    """隐藏代理 URL 中的凭据，仅保留主机与端口。"""

    if "@" not in url:
        return url
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname or "***"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://***:***@{host}{port}"


def _parse_env_file(path: Path) -> Dict[str, str]:
    """读取 .env 文件并返回键值映射。"""

    result: Dict[str, str] = {}
    if not path.exists():
        return result
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    except Exception as exc:  # pylint: disable=broad-except
        log.warning("解析 MASTER_ENV_FILE 失败: %s", exc, extra={"path": str(path)})
    return result


def _dump_env_file(path: Path, values: Dict[str, str]) -> None:
    """写入 .env，默认采用 600 权限。"""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{key}={values[key]}" for key in sorted(values)]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except PermissionError:
            pass
    except Exception as exc:  # pylint: disable=broad-except
        log.warning("写入 MASTER_ENV_FILE 失败: %s", exc, extra={"path": str(path)})


def _update_master_env(chat_id: Optional[int], user_id: Optional[int]) -> None:
    """将最近一次 master 交互信息写入 .env。"""

    if not MASTER_ENV_FILE:
        return
    with _ENV_LOCK:
        env_map = _parse_env_file(MASTER_ENV_FILE)
        changed = False
        if chat_id is not None:
            value = str(chat_id)
            if env_map.get("MASTER_CHAT_ID") != value:
                env_map["MASTER_CHAT_ID"] = value
                changed = True
            os.environ["MASTER_CHAT_ID"] = value
        if user_id is not None:
            value = str(user_id)
            if env_map.get("MASTER_USER_ID") != value:
                env_map["MASTER_USER_ID"] = value
                changed = True
            os.environ["MASTER_USER_ID"] = value
        if changed:
            _dump_env_file(MASTER_ENV_FILE, env_map)


def _format_project_line(cfg: "ProjectConfig", state: Optional[ProjectState]) -> str:
    """格式化项目状态信息，用于日志与通知。"""

    status = state.status if state else "stopped"
    model = state.model if state else cfg.default_model
    chat_id = state.chat_id if state else cfg.allowed_chat_id
    return (
        f"- {cfg.display_name}: status={status}, model={model}, chat_id={chat_id}, project={cfg.project_slug}"
    )


def _projects_overview(manager: MasterManager) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """根据当前项目状态生成概览文本与操作按钮。"""

    builder = InlineKeyboardBuilder()
    button_count = 0
    model_name_map = dict(SWITCHABLE_MODELS)
    for cfg in manager.configs:
        state = manager.state_store.data.get(cfg.project_slug)
        status = state.status if state else "stopped"
        current_model = (state.model if state else cfg.default_model).lower()
        current_model_label = model_name_map.get(current_model, current_model)
        if status == "running":
            builder.row(
                InlineKeyboardButton(
                    text=f"{cfg.display_name}",
                    url=cfg.jump_url,
                ),
                InlineKeyboardButton(
                    text=f"⛔️ 停止 ({current_model_label})",
                    callback_data=f"project:stop:{cfg.project_slug}",
                ),
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cfg.display_name}",
                    url=cfg.jump_url,
                ),
                InlineKeyboardButton(
                    text=f"▶️ 启动 ({current_model_label})",
                    callback_data=f"project:run:{cfg.project_slug}",
                ),
            )
        button_count += 1
    builder.row(
        InlineKeyboardButton(text="🚀 启动全部项目", callback_data="project:start_all:*")
    )
    builder.row(
        InlineKeyboardButton(text="⛔️ 停止全部项目", callback_data="project:stop_all:*")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 重启 Master", callback_data="project:restart_master:*")
    )
    markup = builder.as_markup()
    markup = _ensure_numbered_markup(markup)
    log.info("项目概览生成按钮数量=%s", button_count)
    if button_count == 0:
        return "暂无项目配置，请在“⚙️ 项目管理”创建新项目后再尝试。", markup
    return "请选择操作：", markup


def _detect_proxy() -> Tuple[Optional[str], Optional[BasicAuth], Optional[str]]:
    """从环境变量解析可用的代理配置。"""

    candidates = [
        ("TELEGRAM_PROXY", os.environ.get("TELEGRAM_PROXY")),
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
    from urllib.parse import urlparse
    parsed = urlparse(proxy_raw)
    auth: Optional[BasicAuth] = None
    if parsed.username:
        password = parsed.password or ""
        auth = BasicAuth(parsed.username, password)
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        proxy_raw = parsed._replace(netloc=netloc, path="", params="", query="", fragment="").geturl()
    log.info("使用代理(%s): %s", source, _mask_proxy(proxy_raw))
    return proxy_raw, auth, source


def _sanitize_slug(text: str) -> str:
    """将任意字符串转换为 project_slug 可用的短标签。"""

    slug = text.lower().replace(" ", "-")
    slug = slug.replace("/", "-").replace("\\", "-")
    slug = slug.strip("-")
    return slug or "project"


@dataclass
class ProjectConfig:
    """描述单个项目的静态配置。"""

    bot_name: str
    bot_token: str
    project_slug: str
    default_model: str = "codex"
    workdir: Optional[str] = None
    allowed_chat_id: Optional[int] = None
    legacy_name: Optional[str] = None

    def __post_init__(self) -> None:
        """保证 bot 名称合法，去除多余前缀与空白。"""

        clean_name = self.bot_name.strip()
        if clean_name.startswith("@"):  # 允许配置中直接写带@
            clean_name = clean_name[1:]
        clean_name = clean_name.strip()
        if not clean_name:
            raise ValueError("bot_name 不能为空")
        self.bot_name = clean_name

    @property
    def display_name(self) -> str:
        """返回展示用的 bot 名称。"""

        return self.bot_name

    @property
    def jump_url(self) -> str:
        """生成跳转到 Telegram Bot 的链接。"""

        return f"https://t.me/{self.bot_name}"

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """从 JSON 字典构造 ProjectConfig 实例。"""

        raw_bot_name = data.get("bot_name") or data.get("name")
        if not raw_bot_name:
            raise KeyError("bot_name")
        bot_name = str(raw_bot_name)
        slug_source = data.get("project_slug") or bot_name
        allowed = data.get("allowed_chat_id")
        if isinstance(allowed, str) and allowed.isdigit():
            allowed = int(allowed)
        cfg = cls(
            bot_name=bot_name,
            bot_token=data["bot_token"].strip(),
            project_slug=_sanitize_slug(slug_source),
            default_model=data.get("default_model", "codex"),
            workdir=data.get("workdir"),
            allowed_chat_id=allowed,
            legacy_name=str(data.get("name", "")).strip() or None,
        )
        return cfg


@dataclass
class ProjectState:
    """表示项目当前运行状态，由 StateStore 持久化。"""

    model: str
    status: str = "stopped"
    chat_id: Optional[int] = None


class StateStore:
    """负责维护项目运行状态的文件持久化。"""

    def __init__(self, path: Path, configs: Dict[str, ProjectConfig]):
        """初始化状态存储，加载已有 state 文件并对缺失项使用默认值。"""

        self.path = path
        self.configs = configs  # key 使用 project_slug
        self.data: Dict[str, ProjectState] = {}
        self.refresh()
        self.save()

    def reset_configs(
        self,
        configs: Dict[str, ProjectConfig],
        preserve: Optional[Dict[str, ProjectState]] = None,
    ) -> None:
        """更新配置映射，新增项目时写入默认状态，删除项目时移除记录。"""
        self.configs = configs
        # 移除已删除项目的状态
        for slug in list(self.data.keys()):
            if slug not in configs:
                del self.data[slug]
        # 为新增项目补充默认状态
        for slug, cfg in configs.items():
            if slug not in self.data:
                self.data[slug] = ProjectState(
                    model=cfg.default_model,
                    status="stopped",
                    chat_id=cfg.allowed_chat_id,
                )
        if preserve:
            self.data.update(preserve)
        self.save()

    def refresh(self) -> None:
        """从 state 文件重新加载所有项目状态。"""

        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                log.warning("无法解析 state 文件 %s，使用空状态", self.path)
                raw = {}
        else:
            raw = {}
        for slug, cfg in self.configs.items():
            item = (
                raw.get(slug)
                or raw.get(cfg.bot_name)
                or raw.get(f"@{cfg.bot_name}")
                or (cfg.legacy_name and raw.get(cfg.legacy_name))
                or {}
            )
            model = item.get("model", cfg.default_model)
            status = item.get("status", "stopped")
            chat_id_value = item.get("chat_id", cfg.allowed_chat_id)
            if isinstance(chat_id_value, str) and chat_id_value.isdigit():
                chat_id_value = int(chat_id_value)
            self.data[slug] = ProjectState(model=model, status=status, chat_id=chat_id_value)

    def save(self) -> None:
        """将当前内存状态写入磁盘文件。"""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            slug: {
                "model": state.model,
                "status": state.status,
                "chat_id": state.chat_id,
            }
            for slug, state in self.data.items()
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def update(
        self,
        slug: str,
        *,
        model: Optional[str] = None,
        status: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> None:
        """更新指定项目的状态并立即持久化。"""

        state = self.data[slug]
        if model is not None:
            state.model = model
        if status is not None:
            state.status = status
        if chat_id is not None:
            state.chat_id = chat_id
        self.save()


class MasterManager:
    """封装项目配置、状态持久化与前置检查等核心逻辑。"""

    def __init__(self, configs: List[ProjectConfig], *, state_store: StateStore):
        """构建 manager，并基于配置建立 slug/mention 索引。"""

        self.configs = configs
        self._slug_index: Dict[str, ProjectConfig] = {cfg.project_slug: cfg for cfg in configs}
        self._mention_index: Dict[str, ProjectConfig] = {}
        for cfg in configs:
            self._mention_index[cfg.bot_name] = cfg
            self._mention_index[f"@{cfg.bot_name}"] = cfg
            if cfg.legacy_name:
                self._mention_index[cfg.legacy_name] = cfg
        self.state_store = state_store
        admins = os.environ.get("MASTER_ADMIN_IDS") or os.environ.get("ALLOWED_CHAT_ID", "")
        self.admin_ids = {int(x) for x in admins.split(",") if x.strip().isdigit()}

    def require_project(self, name: str) -> ProjectConfig:
        """根据项目名或 @bot 名查找配置，找不到时报错。"""

        cfg = self._resolve_project(name)
        if not cfg:
            raise ValueError(f"未知项目 {name}")
        return cfg

    def require_project_by_slug(self, slug: str) -> ProjectConfig:
        """根据 project_slug 查找配置。"""

        cfg = self._slug_index.get(slug)
        if not cfg:
            raise ValueError(f"未知项目 {slug}")
        return cfg

    def _resolve_project(self, identifier: str) -> Optional[ProjectConfig]:
        """在 slug/mention 索引中寻找匹配的项目配置。"""

        if not identifier:
            return None
        raw = identifier.strip()
        if not raw:
            return None
        if raw in self._slug_index:
            return self._slug_index[raw]
        if raw in self._mention_index:
            return self._mention_index[raw]
        if raw.startswith("@"):  # 允许用户直接输入 @bot_name
            stripped = raw[1:]
            if stripped in self._mention_index:
                return self._mention_index[stripped]
        else:
            mention_form = f"@{raw}"
            if mention_form in self._mention_index:
                return self._mention_index[mention_form]
        return None

    def rebuild_configs(
        self,
        configs: List[ProjectConfig],
        preserve: Optional[Dict[str, ProjectState]] = None,
    ) -> None:
        """刷新项目配置索引，便于在新增/删除后立即生效。"""
        self.configs = configs
        self._slug_index = {cfg.project_slug: cfg for cfg in configs}
        self._mention_index = {}
        for cfg in configs:
            self._mention_index[cfg.bot_name] = cfg
            self._mention_index[f"@{cfg.bot_name}"] = cfg
            if cfg.legacy_name:
                self._mention_index[cfg.legacy_name] = cfg
        self.state_store.reset_configs({cfg.project_slug: cfg for cfg in configs}, preserve=preserve)

    def refresh_state(self) -> None:
        """从磁盘重新加载项目运行状态。"""

        self.state_store.refresh()

    def list_states(self) -> Dict[str, ProjectState]:
        """返回当前所有项目的状态字典。"""

        return self.state_store.data

    def is_authorized(self, chat_id: int) -> bool:
        """检查给定 chat_id 是否在管理员名单中。"""

        return not self.admin_ids or chat_id in self.admin_ids

    @staticmethod
    def _format_issue_message(title: str, issues: Sequence[str]) -> str:
        """按照项目自检的结果拼装 Markdown 文本。"""

        lines: List[str] = []
        for issue in issues:
            if "\n" in issue:
                first, *rest = issue.splitlines()
                lines.append(f"- {first}")
                lines.extend(f"  {line}" for line in rest)
            else:
                lines.append(f"- {issue}")
        joined = "\n".join(lines) if lines else "- 无"
        return f"{title}\n{joined}"

    def _collect_prerequisite_issues(self, cfg: ProjectConfig, model: str) -> List[str]:
        """检查模型启动前的依赖条件，返回所有未满足的项。"""

        issues: List[str] = []
        workdir_raw = (cfg.workdir or "").strip()
        if not workdir_raw:
            issues.append(
                "未配置 workdir，请通过项目管理功能为该项目设置工作目录"
            )
            expanded_dir = None
        else:
            expanded = Path(os.path.expandvars(os.path.expanduser(workdir_raw)))
            if not expanded.exists():
                issues.append(f"工作目录不存在: {workdir_raw}")
                expanded_dir = None
            elif not expanded.is_dir():
                issues.append(f"工作目录不是文件夹: {workdir_raw}")
                expanded_dir = None
            else:
                expanded_dir = expanded

        if not cfg.bot_token:
            issues.append("bot_token 未配置，请通过项目管理功能补充该字段")

        if shutil.which("tmux") is None:
            issues.append("未检测到 tmux，可通过 'brew install tmux' 安装")

        model_lower = (model or "").lower()
        model_cmd = os.environ.get("MODEL_CMD")
        if not model_cmd:
            if model_lower == "codex":
                model_cmd = os.environ.get("CODEX_CMD") or "codex"
            elif model_lower == "claudecode":
                model_cmd = os.environ.get("CLAUDE_CMD") or "claude"
            elif model_lower == "gemini":
                model_cmd = os.environ.get("GEMINI_CMD") or ""

        if model_cmd:
            try:
                executable = shlex.split(model_cmd)[0]
            except ValueError:
                executable = None
            if executable and shutil.which(executable) is None:
                issues.append(f"未检测到模型命令 {executable}，请确认已安装")
        elif model_lower != "gemini":
            issues.append("未找到模型命令配置，无法启动 worker")

        if expanded_dir is None and workdir_raw:
            log.debug(
                "工作目录校验失败",
                extra={"project": cfg.project_slug, "workdir": workdir_raw},
            )

        return issues

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        """检测指定 PID 的进程是否仍在运行。"""

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        else:
            return True

    def _log_tail(self, path: Path, *, lines: int = WORKER_HEALTH_LOG_TAIL) -> str:
        """读取日志文件尾部，协助诊断启动失败原因。"""

        if not path.exists():
            return ""
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                data = fh.readlines()
        except Exception as exc:
            log.warning(
                "读取日志失败: %s",
                exc,
                extra={"log_path": str(path)},
            )
            return ""
        if not data:
            return ""
        tail = data[-lines:]
        return "".join(tail).rstrip()

    def _log_contains_handshake(self, path: Path) -> bool:
        """判断日志中是否包含 Telegram 握手成功的标记。"""

        if not path.exists():
            return False
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            log.warning(
                "读取日志失败: %s",
                exc,
                extra={"log_path": str(path)},
            )
            return False
        return any(marker in text for marker in HANDSHAKE_MARKERS)

    async def _health_check_worker(self, cfg: ProjectConfig, model: str) -> Optional[str]:
        """验证 worker 启动后的健康状态，返回失败描述。"""

        log_dir = LOG_ROOT_PATH / model / cfg.project_slug
        pid_path = log_dir / "bot.pid"
        run_log = log_dir / "run_bot.log"

        deadline = time.monotonic() + WORKER_HEALTH_TIMEOUT
        last_seen_pid: Optional[int] = None

        while time.monotonic() < deadline:
            if pid_path.exists():
                try:
                    pid_text = pid_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if pid_text:
                        last_seen_pid = int(pid_text)
                        if not self._pid_alive(last_seen_pid):
                            break
                except ValueError:
                    log.warning(
                        "pid 文件 %s 内容异常",
                        str(pid_path),
                        extra={"content": pid_path.read_text(encoding="utf-8", errors="ignore")},
                    )
                    last_seen_pid = None
                except Exception as exc:
                    log.warning(
                        "读取 pid 文件失败: %s",
                        exc,
                        extra={"pid_path": str(pid_path)},
                    )

            if self._log_contains_handshake(run_log):
                return None

            await asyncio.sleep(WORKER_HEALTH_INTERVAL)

        issues: List[str] = []
        if last_seen_pid is None:
            issues.append("未检测到 bot.pid 或内容为空")
        else:
            if self._pid_alive(last_seen_pid):
                issues.append(
                    f"worker 进程 {last_seen_pid} 未在 {WORKER_HEALTH_TIMEOUT:.1f}s 内完成 Telegram 握手"
                )
            else:
                issues.append(f"worker 进程 {last_seen_pid} 已退出")

        log_tail = self._log_tail(run_log)
        if log_tail:
            issues.append(
                "最近日志:\n" + textwrap.indent(log_tail, prefix="  ")
            )

        if not issues:
            return None

        return self._format_issue_message(
            f"{cfg.display_name} 启动失败",
            issues,
        )

    async def run_worker(self, cfg: ProjectConfig, model: Optional[str] = None) -> str:
        """启动指定项目的 worker，并返回运行模型名称。"""

        self.refresh_state()
        state = self.state_store.data[cfg.project_slug]
        target_model = model or state.model or cfg.default_model
        issues = self._collect_prerequisite_issues(cfg, target_model)
        if issues:
            message = self._format_issue_message(
                f"{cfg.display_name} 启动失败，缺少必要依赖或配置",
                issues,
            )
            log.error(
                "启动前自检失败: %s",
                message,
                extra={"project": cfg.project_slug, "model": target_model},
            )
            raise RuntimeError(message)
        chat_id_env = state.chat_id or cfg.allowed_chat_id
        env = os.environ.copy()
        env.update(
            {
                "BOT_TOKEN": cfg.bot_token,
                "MODEL_DEFAULT": target_model,
                "PROJECT_NAME": cfg.project_slug,
                "MODEL_WORKDIR": cfg.workdir or "",
                "CODEX_WORKDIR": cfg.workdir or env.get("CODEX_WORKDIR", ""),
                "CLAUDE_WORKDIR": cfg.workdir or env.get("CLAUDE_WORKDIR", ""),
                "GEMINI_WORKDIR": cfg.workdir or env.get("GEMINI_WORKDIR", ""),
                "STATE_FILE": str(STATE_PATH),
            }
        )
        cmd = [str(RUN_SCRIPT), "--model", target_model, "--project", cfg.project_slug]
        log.info(
            "启动 worker: %s (model=%s, chat_id=%s)",
            cfg.display_name,
            target_model,
            chat_id_env,
            extra={"project": cfg.project_slug, "model": target_model},
        )
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(ROOT_DIR),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        rc = proc.returncode
        output_chunks: List[str] = []
        if stdout_bytes:
            output_chunks.append(stdout_bytes.decode("utf-8", errors="ignore"))
        if stderr_bytes:
            output_chunks.append(stderr_bytes.decode("utf-8", errors="ignore"))
        combined_output = "".join(output_chunks).strip()
        if rc != 0:
            tail_lines = "\n".join(combined_output.splitlines()[-20:]) if combined_output else ""
            issues = [f"run_bot.sh 退出码 {rc}"]
            if tail_lines:
                issues.append("脚本输出:\n  " + "\n  ".join(tail_lines.splitlines()))
            message = self._format_issue_message(
                f"{cfg.display_name} 启动失败",
                issues,
            )
            log.error(
                "worker 启动失败: %s",
                message,
                extra={"project": cfg.project_slug, "model": target_model},
            )
            raise RuntimeError(message)
        health_issue = await self._health_check_worker(cfg, target_model)
        if health_issue:
            self.state_store.update(cfg.project_slug, status="stopped")
            log.error(
                "worker 健康检查失败: %s",
                health_issue,
                extra={"project": cfg.project_slug, "model": target_model},
            )
            raise RuntimeError(health_issue)

        self.state_store.update(cfg.project_slug, model=target_model, status="running")
        return target_model

    async def stop_worker(self, cfg: ProjectConfig, *, update_state: bool = True) -> None:
        """停止指定项目的 worker，必要时刷新状态。"""

        self.refresh_state()
        state = self.state_store.data[cfg.project_slug]
        model = state.model
        cmd = [str(STOP_SCRIPT), "--model", model, "--project", cfg.project_slug]
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=str(ROOT_DIR))
        await proc.wait()
        if update_state:
            self.state_store.update(cfg.project_slug, status="stopped")
        log.info("已停止 worker: %s", cfg.display_name, extra={"project": cfg.project_slug})

    async def stop_all(self, *, update_state: bool = False) -> None:
        """依次停止所有项目的 worker。"""

        for cfg in self.configs:
            try:
                await self.stop_worker(cfg, update_state=update_state)
            except Exception as exc:
                log.warning(
                    "停止 %s 时出错: %s",
                    cfg.display_name,
                    exc,
                    extra={"project": cfg.project_slug},
                )

    async def run_all(self) -> None:
        """启动所有尚未运行的项目 worker。"""

        self.refresh_state()
        errors: List[str] = []
        for cfg in self.configs:
            state = self.state_store.data.get(cfg.project_slug)
            if state and state.status == "running":
                continue
            try:
                await self.run_worker(cfg)
            except Exception as exc:
                log.warning(
                    "启动 %s 时出错: %s",
                    cfg.display_name,
                    exc,
                    extra={"project": cfg.project_slug},
                )
                errors.append(f"{cfg.display_name}: {exc}")
        if errors:
            raise RuntimeError(
                self._format_issue_message("部分项目启动失败", errors)
            )

    async def restore_running(self) -> None:
        """根据 state 文件恢复上一轮仍在运行的 worker。"""

        self.refresh_state()
        for slug, state in self.state_store.data.items():
            if state.status == "running":
                cfg = self._slug_index.get(slug)
                if not cfg:
                    log.warning("状态文件包含未知项目: %s", slug)
                    continue
                try:
                    await self.run_worker(cfg, model=state.model)
                except Exception as exc:
                    log.error(
                        "恢复 %s 失败: %s",
                        cfg.display_name,
                        exc,
                        extra={"project": cfg.project_slug, "model": state.model},
                    )
                    self.state_store.update(slug, status="stopped")

    def update_chat_id(self, slug: str, chat_id: int) -> None:
        """记录或更新项目的 chat_id 绑定信息。"""

        cfg = self._resolve_project(slug)
        if not cfg:
            raise ValueError(f"未知项目 {slug}")
        self.state_store.update(cfg.project_slug, chat_id=chat_id)
        log.info(
            "记录 %s 的 chat_id=%s",
            cfg.display_name,
            chat_id,
            extra={"project": cfg.project_slug},
        )


MANAGER: Optional[MasterManager] = None
PROJECT_REPOSITORY: Optional[ProjectRepository] = None
ProjectField = Literal["bot_name", "bot_token", "project_slug", "default_model", "workdir", "allowed_chat_id"]


@dataclass
class ProjectWizardSession:
    """记录单个聊天的项目管理对话状态。"""

    chat_id: int
    user_id: int
    mode: Literal["create", "edit", "delete"]
    original_slug: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    step_index: int = 0
    original_record: Optional[ProjectRecord] = None
    fields: Tuple[ProjectField, ...] = field(default_factory=tuple)


PROJECT_WIZARD_FIELDS_CREATE: Tuple[ProjectField, ...] = (
    "bot_name",
    "bot_token",
    "default_model",
    "workdir",
)
PROJECT_WIZARD_FIELDS_EDIT: Tuple[ProjectField, ...] = (
    "bot_name",
    "bot_token",
    "project_slug",
    "default_model",
    "workdir",
    "allowed_chat_id",
)
PROJECT_WIZARD_OPTIONAL_FIELDS: Tuple[ProjectField, ...] = ("workdir", "allowed_chat_id")
PROJECT_MODEL_CHOICES: Tuple[str, ...] = ("codex", "claudecode", "gemini")
PROJECT_WIZARD_SESSIONS: Dict[int, ProjectWizardSession] = {}
PROJECT_WIZARD_LOCK = asyncio.Lock()
PROJECT_FIELD_PROMPTS_CREATE: Dict[ProjectField, str] = {
    "bot_name": "请输入 bot 名称（不含 @，仅字母、数字、下划线或点）：",
    "bot_token": "请输入 Telegram Bot Token（格式类似 123456:ABCdef）：",
    "project_slug": "请输入项目 slug（用于日志目录，留空自动根据 bot 名生成）：",
    "default_model": "请输入默认模型（codex/claudecode/gemini，留空采用 codex）：",
    "workdir": "请输入 worker 工作目录绝对路径（可留空稍后补全）：",
    "allowed_chat_id": "请输入预设 chat_id（可留空，暂不支持多个）：",
}
PROJECT_FIELD_PROMPTS_EDIT: Dict[ProjectField, str] = {
    "bot_name": "请输入新的 bot 名（不含 @，发送 - 保持当前值：{current}）：",
    "bot_token": "请输入新的 Bot Token（发送 - 保持当前值）：",
    "project_slug": "请输入新的项目 slug（发送 - 保持当前值：{current}）：",
    "default_model": "请输入新的默认模型（codex/claudecode/gemini，发送 - 保持当前值：{current}）：",
    "workdir": "请输入新的工作目录（发送 - 保持当前值：{current}，可留空改为未设置）：",
    "allowed_chat_id": "请输入新的 chat_id（发送 - 保持当前值：{current}，留空表示取消预设）：",
}


def _ensure_repository() -> ProjectRepository:
    """获取项目仓库实例，未初始化时抛出异常。"""
    if PROJECT_REPOSITORY is None:
        raise RuntimeError("项目仓库未初始化")
    return PROJECT_REPOSITORY


def _reload_manager_configs(
    manager: MasterManager,
    *,
    preserve: Optional[Dict[str, ProjectState]] = None,
) -> List[ProjectConfig]:
    """重新加载项目配置，并可选地保留指定状态映射。"""
    repository = _ensure_repository()
    records = repository.list_projects()
    configs = [ProjectConfig.from_dict(record.to_dict()) for record in records]
    manager.rebuild_configs(configs, preserve=preserve)
    return configs


def _validate_field_value(
    session: ProjectWizardSession,
    field_name: ProjectField,
    raw_text: str,
) -> Tuple[Optional[Any], Optional[str]]:
    """校验字段输入，返回转换后的值与错误信息。"""
    text = raw_text.strip()
    repository = _ensure_repository()
    # 编辑流程允许使用 "-" 保持原值
    if session.mode == "edit" and text == "-":
        return session.data.get(field_name), None

    if field_name in PROJECT_WIZARD_OPTIONAL_FIELDS and not text:
        return None, None

    if field_name == "bot_name":
        candidate = text.lstrip("@").strip()
        if not candidate:
            return None, "bot 名不能为空"
        if not re.fullmatch(r"[A-Za-z0-9_.]{5,64}", candidate):
            return None, "bot 名仅允许 5-64 位字母、数字、下划线或点"
        existing = repository.get_by_bot_name(candidate)
        if existing and (session.mode == "create" or existing.project_slug != session.original_slug):
            return None, "该 bot 名已被其它项目占用"
        return candidate, None

    if field_name == "bot_token":
        if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,128}", text):
            return None, "Bot Token 格式不正确，请确认输入"
        return text, None

    if field_name == "project_slug":
        candidate = _sanitize_slug(text or session.data.get("bot_name", ""))
        if not candidate:
            return None, "无法生成有效的 slug，请重新输入"
        existing = repository.get_by_slug(candidate)
        if existing and (session.mode == "create" or existing.project_slug != session.original_slug):
            return None, "该 slug 已存在，请更换其它名称"
        return candidate, None

    if field_name == "default_model":
        candidate = text.lower() if text else "codex"
        if candidate not in PROJECT_MODEL_CHOICES:
            return None, f"默认模型仅支持 {', '.join(PROJECT_MODEL_CHOICES)}"
        return candidate, None

    if field_name == "workdir":
        expanded = os.path.expandvars(os.path.expanduser(text))
        path = Path(expanded)
        if not path.exists() or not path.is_dir():
            return None, f"目录不存在或不可用：{text}"
        return str(path), None

    if field_name == "allowed_chat_id":
        if not re.fullmatch(r"-?\d+", text):
            return None, "chat_id 需为整数，可留空跳过"
        return int(text), None

    return text, None


def _format_field_prompt(
    session: ProjectWizardSession, field_name: ProjectField
) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """根据流程生成字段提示语与可选操作键盘。"""

    if session.mode == "edit":
        current_value = session.data.get(field_name)
        if current_value is None:
            display = "未设置"
        elif field_name == "bot_token":
            display = f"{str(current_value)[:6]}***"
        else:
            display = str(current_value)
        template = PROJECT_FIELD_PROMPTS_EDIT[field_name]
        prompt = template.format(current=display)
    else:
        prompt = PROJECT_FIELD_PROMPTS_CREATE[field_name]

    markup: Optional[InlineKeyboardMarkup] = None
    skip_enabled = False
    if field_name in {"workdir", "allowed_chat_id"}:
        skip_enabled = True
    elif field_name == "default_model" and session.mode == "create":
        skip_enabled = True

    if skip_enabled:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="跳过此项",
            callback_data=f"project:wizard:skip:{field_name}",
        )
        markup = builder.as_markup()

    return prompt, markup


async def _send_field_prompt(
    session: ProjectWizardSession,
    field_name: ProjectField,
    target_message: Message,
    *,
    prefix: str = "",
) -> None:
    """向用户发送当前字段的提示语与可选跳过按钮。"""

    prompt, markup = _format_field_prompt(session, field_name)
    if prefix:
        text = f"{prefix}\n{prompt}"
    else:
        text = prompt
    await target_message.answer(text, reply_markup=markup)


def _session_to_record(session: ProjectWizardSession) -> ProjectRecord:
    """将会话数据转换为 ProjectRecord，编辑时保留 legacy_name。"""
    legacy_name = session.original_record.legacy_name if session.original_record else None
    return ProjectRecord(
        bot_name=session.data["bot_name"],
        bot_token=session.data["bot_token"],
        project_slug=session.data.get("project_slug") or _sanitize_slug(session.data["bot_name"]),
        default_model=session.data["default_model"],
        workdir=session.data.get("workdir"),
        allowed_chat_id=session.data.get("allowed_chat_id"),
        legacy_name=legacy_name,
    )


async def _commit_wizard_session(
    session: ProjectWizardSession,
    manager: MasterManager,
    message: Message,
) -> bool:
    """提交会话数据并执行仓库写入。"""
    repository = _ensure_repository()
    record = _session_to_record(session)
    try:
        if session.mode == "create":
            repository.insert_project(record)
            _reload_manager_configs(manager)
            summary_prefix = "新增项目成功 ✅"
        elif session.mode == "edit":
            original_slug = session.original_slug or record.project_slug
            preserve: Optional[Dict[str, ProjectState]] = None
            old_state = manager.state_store.data.get(original_slug)
            if original_slug != record.project_slug and old_state is not None:
                preserve = {record.project_slug: old_state}
            repository.update_project(original_slug, record)
            if original_slug != record.project_slug and original_slug in manager.state_store.data:
                del manager.state_store.data[original_slug]
            _reload_manager_configs(manager, preserve=preserve)
            summary_prefix = "项目已更新 ✅"
        else:
            return False
    except Exception as exc:
        log.error("项目写入失败: %s", exc, extra={"mode": session.mode})
        await message.answer(f"保存失败：{exc}")
        return False

    workdir_desc = record.workdir or "未设置"
    chat_desc = record.allowed_chat_id if record.allowed_chat_id is not None else "未设置"
    summary = (
        f"{summary_prefix}\n"
        f"bot：@{record.bot_name}\n"
        f"slug：{record.project_slug}\n"
        f"模型：{record.default_model}\n"
        f"工作目录：{workdir_desc}\n"
        f"chat_id：{chat_desc}"
    )
    await message.answer(summary)
    await _send_projects_overview_to_chat(message.bot, message.chat.id, manager)
    return True


async def _advance_wizard_session(
    session: ProjectWizardSession,
    manager: MasterManager,
    message: Message,
    text: str,
    *,
    prefix: str = "已记录 ✅",
) -> bool:
    """推进项目管理流程，校验输入并触发后续步骤。"""

    if session.step_index >= len(session.fields):
        await message.answer("流程已完成，如需再次修改请重新开始。")
        return True

    if not session.fields:
        await message.answer("流程配置异常，请重新开始。")
        async with PROJECT_WIZARD_LOCK:
            PROJECT_WIZARD_SESSIONS.pop(message.chat.id, None)
        return True

    field_name = session.fields[session.step_index]
    value, error = _validate_field_value(session, field_name, text)
    if error:
        await message.answer(f"{error}\n请重新输入：")
        return True

    session.data[field_name] = value
    session.step_index += 1

    if session.mode == "create" and field_name == "bot_name":
        repository = _ensure_repository()
        base_slug = _sanitize_slug(session.data["bot_name"])
        candidate = base_slug
        suffix = 1
        while repository.get_by_slug(candidate):
            suffix += 1
            candidate = f"{base_slug}-{suffix}"
        session.data["project_slug"] = candidate

    if session.step_index < len(session.fields):
        next_field = session.fields[session.step_index]
        await _send_field_prompt(session, next_field, message, prefix=prefix)
        return True

    # 所有字段已填写，执行写入
    success = await _commit_wizard_session(session, manager, message)
    async with PROJECT_WIZARD_LOCK:
        PROJECT_WIZARD_SESSIONS.pop(message.chat.id, None)

    if success:
        await message.answer("项目管理流程已完成。")
    return True


async def _start_project_create(callback: CallbackQuery, manager: MasterManager) -> None:
    """启动新增项目流程。"""
    if callback.message is None or callback.from_user is None:
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    async with PROJECT_WIZARD_LOCK:
        if chat_id in PROJECT_WIZARD_SESSIONS:
            await callback.answer("当前会话已有流程进行中，请先完成或发送“取消”。", show_alert=True)
            return
        session = ProjectWizardSession(
            chat_id=chat_id,
            user_id=user_id,
            mode="create",
            fields=PROJECT_WIZARD_FIELDS_CREATE,
        )
        PROJECT_WIZARD_SESSIONS[chat_id] = session
    await callback.answer("开始新增项目流程")
    await callback.message.answer(
        "已进入新增项目流程，随时可发送“取消”终止。",
    )
    first_field = session.fields[0]
    await _send_field_prompt(session, first_field, callback.message)


async def _start_project_edit(
    callback: CallbackQuery,
    cfg: ProjectConfig,
    manager: MasterManager,
) -> None:
    """启动项目编辑流程。"""
    if callback.message is None or callback.from_user is None:
        return
    repository = _ensure_repository()
    record = repository.get_by_slug(cfg.project_slug)
    if record is None:
        await callback.answer("未找到项目配置", show_alert=True)
        return
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    async with PROJECT_WIZARD_LOCK:
        if chat_id in PROJECT_WIZARD_SESSIONS:
            await callback.answer("当前会话已有流程进行中，请先完成或发送“取消”。", show_alert=True)
            return
        session = ProjectWizardSession(
            chat_id=chat_id,
            user_id=user_id,
            mode="edit",
            original_slug=cfg.project_slug,
            original_record=record,
            fields=PROJECT_WIZARD_FIELDS_EDIT,
        )
        session.data = {
            "bot_name": record.bot_name,
            "bot_token": record.bot_token,
            "project_slug": record.project_slug,
            "default_model": record.default_model,
            "workdir": record.workdir,
            "allowed_chat_id": record.allowed_chat_id,
        }
        PROJECT_WIZARD_SESSIONS[chat_id] = session
    await callback.answer("开始编辑项目")
    await callback.message.answer(
        f"已进入编辑流程：{cfg.display_name}，随时可发送“取消”终止。",
    )
    field_name = session.fields[0]
    await _send_field_prompt(session, field_name, callback.message)


def _build_delete_confirmation_keyboard(slug: str) -> InlineKeyboardMarkup:
    """构建删除确认用的按钮键盘。"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="确认删除 ✅",
            callback_data=f"project:delete_confirm:{slug}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="取消",
            callback_data="project:delete_cancel",
        )
    )
    markup = builder.as_markup()
    return _ensure_numbered_markup(markup)


async def _start_project_delete(
    callback: CallbackQuery,
    cfg: ProjectConfig,
    manager: MasterManager,
    state: FSMContext,
) -> None:
    """启动删除项目的确认流程。"""
    if callback.message is None or callback.from_user is None:
        return
    repository = _ensure_repository()
    original_record = repository.get_by_slug(cfg.project_slug)
    original_slug = original_record.project_slug if original_record else cfg.project_slug
    project_state = manager.state_store.data.get(cfg.project_slug)
    if project_state and project_state.status == "running":
        await callback.answer("请先停止该项目的 worker 后再删除。", show_alert=True)
        return
    current_state = await state.get_state()
    if current_state == ProjectDeleteStates.confirming.state:
        data = await state.get_data()
        existing_slug = str(data.get("project_slug", "")).lower()
        if existing_slug == cfg.project_slug.lower():
            await callback.answer("当前删除流程已在确认中，请使用按钮完成操作。", show_alert=True)
            return
        await state.clear()
    await state.set_state(ProjectDeleteStates.confirming)
    await state.update_data(
        project_slug=cfg.project_slug,
        display_name=cfg.display_name,
        initiator_id=callback.from_user.id,
        expires_at=time.time() + DELETE_CONFIRM_TIMEOUT,
        original_slug=original_slug,
        bot_name=cfg.bot_name,
    )
    markup = _build_delete_confirmation_keyboard(cfg.project_slug)
    await callback.answer("删除确认已发送")
    await callback.message.answer(
        f"确认删除项目 {cfg.display_name}？此操作不可恢复。\n"
        f"请在 {DELETE_CONFIRM_TIMEOUT} 秒内使用下方按钮确认或取消。",
        reply_markup=markup,
    )


async def _handle_wizard_message(
    message: Message,
    manager: MasterManager,
) -> bool:
    """处理项目管理流程中的用户输入。"""
    if message.chat is None or message.from_user is None:
        return False
    chat_id = message.chat.id
    async with PROJECT_WIZARD_LOCK:
        session = PROJECT_WIZARD_SESSIONS.get(chat_id)
    if session is None:
        return False
    if message.from_user.id != session.user_id:
        await message.answer("仅流程发起者可以继续操作。")
        return True
    text = (message.text or "").strip()
    if text.lower() in {"取消", "cancel", "/cancel"}:
        async with PROJECT_WIZARD_LOCK:
            PROJECT_WIZARD_SESSIONS.pop(chat_id, None)
        await message.answer("已取消项目管理流程。")
        return True

    return await _advance_wizard_session(session, manager, message, text)
router = Router()
log = create_logger("master", level_env="MASTER_LOG_LEVEL", stderr_env="MASTER_STDERR")

# 重启状态锁与标记，避免重复触发
_restart_lock: Optional[asyncio.Lock] = None
_restart_in_progress: bool = False


def _ensure_restart_lock() -> asyncio.Lock:
    """延迟创建 asyncio.Lock，确保在事件循环内初始化"""
    global _restart_lock
    if _restart_lock is None:
        _restart_lock = asyncio.Lock()
    return _restart_lock


def _log_update(message: Message, *, override_user: Optional[User] = None) -> None:
    """记录每条更新并同步 MASTER_ENV_FILE 中的最近聊天信息。"""

    user = override_user or message.from_user
    username = user.username if user and user.username else None
    log.info(
        "update chat=%s user=%s username=%s text=%s",
        message.chat.id,
        user.id if user else None,
        username,
        message.text,
    )
    chat_id = message.chat.id
    user_id = user.id if user else None
    _update_master_env(chat_id, user_id)


def _safe_remove(path: Path) -> None:
    """安全移除文件，忽略不存在的情况"""
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except Exception as exc:
        log.warning("删除文件失败: %s", exc, extra={"path": str(path)})


def _write_restart_signal(message: Message, *, override_user: Optional[User] = None) -> None:
    """将重启请求信息写入 signal 文件，供新 master 启动后读取"""
    now_local = datetime.now(LOCAL_TZ)
    actor = override_user or message.from_user
    payload = {
        "chat_id": message.chat.id,
        "user_id": actor.id if actor else None,
        "username": actor.username if actor and actor.username else None,
        "timestamp": now_local.isoformat(),
        "message_id": message.message_id,
    }
    RESTART_SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = RESTART_SIGNAL_PATH.with_suffix(RESTART_SIGNAL_PATH.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tmp_path.replace(RESTART_SIGNAL_PATH)
    log.info(
        "已记录重启信号: chat_id=%s user_id=%s 文件=%s",
        payload["chat_id"],
        payload["user_id"],
        RESTART_SIGNAL_PATH,
        extra={"chat": payload["chat_id"]},
    )


def _read_restart_signal() -> Optional[dict]:
    """读取并验证重启 signal，超时会自动清理"""
    if not RESTART_SIGNAL_PATH.exists():
        return None
    try:
        raw = json.loads(RESTART_SIGNAL_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("signal payload 必须是对象")
    except Exception as exc:
        log.error("读取重启信号失败: %s", exc)
        _safe_remove(RESTART_SIGNAL_PATH)
        return None

    timestamp_raw = raw.get("timestamp")
    if timestamp_raw:
        try:
            ts = datetime.fromisoformat(timestamp_raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=LOCAL_TZ)
            ts_utc = ts.astimezone(timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - ts_utc).total_seconds()
            if age_seconds > RESTART_SIGNAL_TTL:
                log.info(
                    "重启信号超时，忽略",
                    extra={
                        "path": str(RESTART_SIGNAL_PATH),
                        "age_seconds": age_seconds,
                        "ttl": RESTART_SIGNAL_TTL,
                    },
                )
                _safe_remove(RESTART_SIGNAL_PATH)
                return None
        except Exception as exc:
            log.warning("解析重启信号时间戳失败: %s", exc)

    return raw


async def _notify_restart_success(bot: Bot) -> None:
    """在新 master 启动时读取 signal 并通知触发者"""
    restart_expected = os.environ.pop("MASTER_RESTART_EXPECTED", None)
    payload = _read_restart_signal()
    if not payload:
        if restart_expected:
            targets = _collect_admin_targets()
            log.warning(
                "启动时未检测到重启信号文件，将向管理员发送兜底提醒", extra={"targets": targets}
            )
            if targets:
                text = (
                    "Master 已重新上线，但未找到重启触发者信息。"
                    "可能是重启信号写入失败，请确认服务状态。"
                )
                for chat in targets:
                    try:
                        await bot.send_message(chat_id=chat, text=text)
                    except Exception as exc:
                        log.error("发送兜底重启通知失败: %s", exc, extra={"chat": chat})
        else:
            log.info("启动时未检测到重启信号文件，可能是正常启动。")
        return

    chat_id_raw = payload.get("chat_id")
    try:
        chat_id = int(chat_id_raw)
    except (TypeError, ValueError):
        log.error("重启信号 chat_id 非法: %s", chat_id_raw)
        _safe_remove(RESTART_SIGNAL_PATH)
        return

    username = payload.get("username")
    user_id = payload.get("user_id")
    timestamp = payload.get("timestamp")
    timestamp_fmt: Optional[str] = None
    if timestamp:
        try:
            ts = datetime.fromisoformat(timestamp)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=LOCAL_TZ)
            ts_local = ts.astimezone(LOCAL_TZ)
            timestamp_fmt = ts_local.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception as exc:
            log.warning("解析重启时间失败: %s", exc)

    details = []
    if username:
        details.append(f"触发人：@{username}")
    elif user_id:
        details.append(f"触发人ID：{user_id}")
    if timestamp_fmt:
        details.append(f"请求时间：{timestamp_fmt}")

    message_lines = ["master 已重新上线 ✅"]
    if details:
        message_lines.extend(details)

    text = "\n".join(message_lines)

    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as exc:
        log.error("发送重启成功通知失败: %s", exc, extra={"chat": chat_id})
    else:
        # 重启成功后不再附带项目列表，避免高频重启时产生额外噪音
        log.info("重启成功通知已发送", extra={"chat": chat_id})
    finally:
        _safe_remove(RESTART_SIGNAL_PATH)


async def _ensure_manager() -> MasterManager:
    """确保 MANAGER 已初始化，未初始化时抛出异常。"""

    global MANAGER
    if MANAGER is None:
        raise RuntimeError("Master manager 未初始化")
    return MANAGER


async def _process_restart_request(
    message: Message,
    *,
    trigger_user: Optional[User] = None,
    manager: Optional[MasterManager] = None,
) -> None:
    """响应 /restart 请求，写入重启信号并触发脚本。"""

    if manager is None:
        manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return

    lock = _ensure_restart_lock()
    async with lock:
        global _restart_in_progress
        if _restart_in_progress:
            await message.answer("已有重启请求在执行，请稍候再试。")
            return
        _restart_in_progress = True

    start_script = ROOT_DIR / "scripts/start.sh"
    if not start_script.exists():
        async with lock:
            _restart_in_progress = False
        await message.answer("未找到 ./start.sh，无法执行重启。")
        return

    signal_error: Optional[str] = None
    try:
        _write_restart_signal(message, override_user=trigger_user)
    except Exception as exc:
        signal_error = str(exc)
        log.error("记录重启信号异常: %s", exc)

    notice = (
        "已收到重启指令，运行期间 master 会短暂离线，重启后所有 worker 需稍后手动启动。"
    )
    if signal_error:
        notice += (
            "\n⚠️ 重启信号写入失败，可能无法在重启完成后自动通知。原因: "
            f"{signal_error}"
        )

    await message.answer(notice)

    asyncio.create_task(_perform_restart(message, start_script))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """处理 /start 命令，返回项目概览与状态。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    manager.refresh_state()
    await message.answer(
        "Master bot 已启动。\n"
        f"已登记项目: {len(manager.configs)} 个。\n"
        "使用 /projects 查看状态，/run 或 /stop 控制 worker。",
        reply_markup=_build_master_main_keyboard(),
    )
    await _send_projects_overview_to_chat(
        message.bot,
        message.chat.id,
        manager,
        reply_to_message_id=message.message_id,
    )


async def _perform_restart(message: Message, start_script: Path) -> None:
    """异步执行 ./start.sh，若失败则回滚标记并通知管理员"""
    global _restart_in_progress
    lock = _ensure_restart_lock()
    bot = message.bot
    chat_id = message.chat.id
    await asyncio.sleep(1.0)
    env = os.environ.copy()
    env["MASTER_RESTART_EXPECTED"] = "1"
    notice_error: Optional[Exception] = None
    try:
        await bot.send_message(
            chat_id=chat_id,
            text="开始重启，当前 master 将退出并重新拉起，请稍候。",
        )
    except Exception as notice_exc:
        notice_error = notice_exc
        log.warning("发送启动通知失败: %s", notice_exc)
    try:
        # 使用 DEVNULL 避免继承当前 stdout/stderr，防止父进程退出导致 start.sh 写入管道时触发 BrokenPipe。
        proc = subprocess.Popen(
            ["/bin/bash", str(start_script)],
            cwd=str(ROOT_DIR),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("已触发 start.sh 进行重启，pid=%s", proc.pid if proc else "-")
    except Exception as exc:
        log.error("执行 ./start.sh 失败: %s", exc)
        async with lock:
            _restart_in_progress = False
        try:
            await bot.send_message(chat_id=chat_id, text=f"执行 ./start.sh 失败：{exc}")
        except Exception as send_exc:
            log.error("发送重启失败通知时出错: %s", send_exc)
        return
    else:
        if notice_error:
            log.warning("启动通知未送达，已继续执行 start.sh")
        async with lock:
            _restart_in_progress = False
            log.debug("重启执行中，已提前重置状态标记")


@router.message(Command("restart"))
async def cmd_restart(message: Message) -> None:
    """处理 /restart 命令，触发 master 重启。"""

    _log_update(message)
    await _process_restart_request(message)


async def _send_projects_overview_to_chat(
    bot: Bot,
    chat_id: int,
    manager: MasterManager,
    reply_to_message_id: Optional[int] = None,
) -> None:
    """向指定聊天发送项目概览及操作按钮。"""

    manager.refresh_state()
    try:
        text, markup = _projects_overview(manager)
    except Exception as exc:
        log.exception("生成项目概览失败: %s", exc)
        await bot.send_message(
            chat_id=chat_id,
            text="项目列表生成失败，请稍后再试。",
            reply_to_message_id=reply_to_message_id,
        )
        return
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            reply_to_message_id=reply_to_message_id,
        )
    except TelegramBadRequest as exc:
        log.error("发送项目概览失败: %s", exc)
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
        )
    except Exception as exc:
        log.exception("发送项目概览触发异常: %s", exc)
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
        )
    else:
        log.info("已发送项目概览，按钮=%s", "无" if markup is None else "有")


async def _refresh_project_overview(
    message: Optional[Message],
    manager: MasterManager,
) -> None:
    """在原消息上刷新项目概览，无法编辑时发送新消息。"""

    if message is None:
        return
    manager.refresh_state()
    try:
        text, markup = _projects_overview(manager)
    except Exception as exc:
        log.exception("刷新项目概览失败: %s", exc)
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        log.warning("编辑项目概览失败，将发送新消息: %s", exc)
        try:
            await message.answer(text, reply_markup=markup)
        except Exception as send_exc:
            log.exception("发送项目概览失败: %s", send_exc)


@router.message(Command("projects"))
async def cmd_projects(message: Message) -> None:
    """处理 /projects 命令，返回最新项目概览。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    await _send_projects_overview_to_chat(
        message.bot,
        message.chat.id,
        manager,
        reply_to_message_id=message.message_id,
    )


async def _run_and_reply(message: Message, action: str, coro) -> None:
    """执行异步操作并统一回复成功或失败提示。"""

    try:
        result = await coro
    except Exception as exc:
        log.error("%s 失败: %s", action, exc)
        await message.answer(f"{action} 失败: {exc}")
    else:
        reply_text: str
        reply_markup: Optional[InlineKeyboardMarkup] = None
        if isinstance(result, tuple):
            reply_text = result[0]
            if len(result) > 1:
                reply_markup = result[1]
        else:
            reply_text = result if isinstance(result, str) else f"{action} 完成"
        await message.answer(reply_text, reply_markup=_ensure_numbered_markup(reply_markup))


@router.callback_query(F.data.startswith("project:"))
async def on_project_action(callback: CallbackQuery, state: FSMContext) -> None:
    """处理项目管理相关的回调按钮。"""

    manager = await _ensure_manager()
    user_id = callback.from_user.id if callback.from_user else None
    if user_id is None or not manager.is_authorized(user_id):
        await callback.answer("未授权。", show_alert=True)
        return
    data = callback.data or ""
    # 跳过删除确认/取消，让专用处理器接管，避免误判为未知操作。
    if data.startswith("project:delete_confirm:") or data == "project:delete_cancel":
        raise SkipHandler()
    parts = data.split(":")
    if len(parts) < 3:
        await callback.answer("无效操作", show_alert=True)
        return
    _, action, *rest = parts
    identifier = rest[0] if rest else "*"
    extra_args = rest[1:]
    target_model: Optional[str] = None
    project_slug = identifier
    if action == "switch_to":
        target_model = identifier
        project_slug = extra_args[0] if extra_args else ""
    elif action == "switch_all_to":
        target_model = identifier
        project_slug = "*"

    if action == "refresh":
        # 刷新列表属于全局操作，不依赖具体项目 slug
        if callback.message:
            _reload_manager_configs(manager)
            manager.refresh_state()
            text, markup = _projects_overview(manager)
            await callback.message.edit_text(
                text,
                reply_markup=_ensure_numbered_markup(markup),
            )
        await callback.answer()
        return

    try:
        if action in {"stop_all", "start_all", "restart_master", "create", "switch_all", "switch_all_to"}:
            cfg = None
        else:
            cfg = manager.require_project_by_slug(project_slug)
    except ValueError:
        await callback.answer("未知项目", show_alert=True)
        return

    state = manager.state_store.data.get(cfg.project_slug) if cfg else None
    model_name_map = dict(SWITCHABLE_MODELS)

    if cfg:
        log.info(
            "按钮操作请求: user=%s action=%s project=%s",
            user_id,
            action,
            cfg.display_name,
            extra={"project": cfg.project_slug},
        )
    else:
        log.info("按钮操作请求: user=%s action=%s 所有项目", user_id, action)

    if action == "switch_all":
        builder = InlineKeyboardBuilder()
        for value, label in SWITCHABLE_MODELS:
            builder.row(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"project:switch_all_to:{value}:*",
                )
            )
        builder.row(
            InlineKeyboardButton(
                text="⬅️ 取消",
                callback_data="project:refresh:*",
            )
        )
        await callback.answer()
        await callback.message.answer(
            "请选择全局模型：",
            reply_markup=_ensure_numbered_markup(builder.as_markup()),
        )
        return

    if action == "manage":
        if cfg is None or callback.message is None:
            await callback.answer("未知项目", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📝 编辑",
                callback_data=f"project:edit:{cfg.project_slug}",
            )
        )
        current_model_value = state.model if state else cfg.default_model
        current_model_key = (current_model_value or "").lower()
        current_model_label = model_name_map.get(current_model_key, current_model_value or current_model_key or "-")
        builder.row(
            InlineKeyboardButton(
                text=f"🧠 切换模型（当前模型 {current_model_label}）",
                callback_data=f"project:switch_prompt:{cfg.project_slug}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 删除",
                callback_data=f"project:delete:{cfg.project_slug}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⬅️ 返回项目列表",
                callback_data="project:refresh:*",
            )
        )
        markup = builder.as_markup()
        _ensure_numbered_markup(markup)
        await callback.answer()
        await callback.message.answer(
            f"项目 {cfg.display_name} 的管理操作：",
            reply_markup=markup,
        )
        return

    if action == "switch_prompt":
        if cfg is None or callback.message is None:
            await callback.answer("未知项目", show_alert=True)
            return
        current_model = (state.model if state else cfg.default_model).lower()
        builder = InlineKeyboardBuilder()
        for value, label in SWITCHABLE_MODELS:
            prefix = "✅ " if current_model == value else ""
            builder.row(
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"project:switch_to:{value}:{cfg.project_slug}",
                )
            )
        builder.row(
            InlineKeyboardButton(
                text="⬅️ 返回项目列表",
                callback_data="project:refresh:*",
            )
        )
        markup = builder.as_markup()
        _ensure_numbered_markup(markup)
        await callback.answer()
        await callback.message.answer(
            f"请选择 {cfg.display_name} 要使用的模型：",
            reply_markup=markup,
        )
        return

    if action == "edit":
        if cfg is None:
            await callback.answer("未知项目", show_alert=True)
            return
        await _start_project_edit(callback, cfg, manager)
        return

    if action == "delete":
        if cfg is None:
            await callback.answer("未知项目", show_alert=True)
            return
        await _start_project_delete(callback, cfg, manager, state)
        return

    if action == "create":
        await _start_project_create(callback, manager)
        return

    if action == "restart_master":
        await callback.answer("已收到重启指令")

    try:
        if action == "stop_all":
            await manager.stop_all(update_state=True)
            log.info("按钮操作成功: user=%s 停止全部项目", user_id)
        elif action == "start_all":
            await manager.run_all()
            log.info("按钮操作成功: user=%s 启动全部项目", user_id)
            await callback.answer("全部项目已启动，正在刷新列表…")
        elif action == "restart_master":
            if callback.message is None:
                log.error("重启按钮回调缺少 message 对象", extra={"user": user_id})
                return
            _log_update(callback.message, override_user=callback.from_user)
            await _process_restart_request(
                callback.message,
                trigger_user=callback.from_user,
                manager=manager,
            )
            log.info("按钮操作成功: user=%s 重启 master", user_id)
        elif action == "run":
            chosen = await manager.run_worker(cfg)
            log.info(
                "按钮操作成功: user=%s 启动 %s (model=%s)",
                user_id,
                cfg.display_name,
                chosen,
                extra={"project": cfg.project_slug, "model": chosen},
            )
            await callback.answer("项目已启动，正在刷新列表…")
        elif action == "stop":
            await manager.stop_worker(cfg)
            log.info(
                "按钮操作成功: user=%s 停止 %s",
                user_id,
                cfg.display_name,
                extra={"project": cfg.project_slug},
            )
            await callback.answer("项目已停止，正在刷新列表…")
        elif action == "switch_all_to":
            model_map = dict(SWITCHABLE_MODELS)
            if target_model not in model_map:
                await callback.answer("不支持的模型", show_alert=True)
                return
            await callback.answer("全局切换中，请稍候…")
            errors: list[tuple[str, str]] = []
            updated: list[str] = []
            for project_cfg in manager.configs:
                try:
                    await manager.stop_worker(project_cfg, update_state=True)
                except Exception as exc:
                    errors.append((project_cfg.display_name, str(exc)))
                    continue
                manager.state_store.update(project_cfg.project_slug, model=target_model, status="stopped")
                updated.append(project_cfg.display_name)
            manager.state_store.save()
            label = model_map[target_model]
            if errors:
                failure_lines = "\n".join(f"- {name}: {err}" for name, err in errors)
                message_text = (
                    f"已尝试将全部项目模型切换为 {label}，但部分项目执行失败：\n{failure_lines}"
                )
                log.warning(
                    "全局模型切换部分失败: user=%s model=%s failures=%s",
                    user_id,
                    target_model,
                    [name for name, _ in errors],
                )
            else:
                message_text = f"所有项目模型已切换为 {label}，并保持停止状态。"
                log.info(
                    "按钮操作成功: user=%s 全部切换模型至 %s",
                    user_id,
                    target_model,
                )
            await callback.message.answer(message_text)
        elif action == "switch_to":
            model_map = dict(SWITCHABLE_MODELS)
            if target_model not in model_map:
                await callback.answer("不支持的模型", show_alert=True)
                return
            state = manager.state_store.data.get(cfg.project_slug)
            previous_model = state.model if state else cfg.default_model
            was_running = bool(state and state.status == "running")
            try:
                if was_running:
                    await manager.stop_worker(cfg, update_state=True)
                manager.state_store.update(cfg.project_slug, model=target_model)
                if was_running:
                    chosen = await manager.run_worker(cfg, model=target_model)
                else:
                    chosen = target_model
            except Exception:
                manager.state_store.update(cfg.project_slug, model=previous_model)
                if was_running:
                    try:
                        await manager.run_worker(cfg, model=previous_model)
                    except Exception as restore_exc:
                        log.error(
                            "模型切换失败且恢复失败: %s",
                            restore_exc,
                            extra={"project": cfg.project_slug, "model": previous_model},
                        )
                raise
            else:
                if was_running:
                    await callback.answer(f"已切换至 {model_map.get(chosen, chosen)}")
                    log.info(
                        "按钮操作成功: user=%s 将 %s 切换至 %s",
                        user_id,
                        cfg.display_name,
                        chosen,
                        extra={"project": cfg.project_slug, "model": chosen},
                    )
                else:
                    await callback.answer(f"默认模型已更新为 {model_map.get(chosen, chosen)}")
                    log.info(
                        "按钮操作成功: user=%s 更新 %s 默认模型为 %s",
                        user_id,
                        cfg.display_name,
                        chosen,
                        extra={"project": cfg.project_slug, "model": chosen},
                    )
        else:
            await callback.answer("未知操作", show_alert=True)
            return
    except Exception as exc:
        log.error(
            "按钮操作失败: action=%s project=%s error=%s",
            action,
            (cfg.display_name if cfg else "*"),
            exc,
            extra={"project": cfg.project_slug if cfg else "*"},
        )
        if callback.message:
            await callback.message.answer(f"操作失败: {exc}")
        await callback.answer("操作失败", show_alert=True)
        return

    await _refresh_project_overview(callback.message, manager)


@router.message(Command("run"))
async def cmd_run(message: Message) -> None:
    """处理 /run 命令，启动指定项目并可选切换模型。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("用法: /run <project> [model]")
        return
    project_raw = parts[1]
    model = parts[2] if len(parts) >= 3 else None
    try:
        cfg = manager.require_project(project_raw)
    except ValueError as exc:
        await message.answer(str(exc))
        return

    async def runner():
        """调用 manager.run_worker 启动项目并返回提示文本。"""

        chosen = await manager.run_worker(cfg, model=model)
        return f"已启动 {cfg.display_name} (model={chosen})"

    await _run_and_reply(message, "启动", runner())


@router.message(Command("stop"))
async def cmd_stop(message: Message) -> None:
    """处理 /stop 命令，停止指定项目。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("用法: /stop <project>")
        return
    project_raw = parts[1]
    try:
        cfg = manager.require_project(project_raw)
    except ValueError as exc:
        await message.answer(str(exc))
        return

    async def stopper():
        """停止指定项目并更新状态。"""

        await manager.stop_worker(cfg, update_state=True)
        return f"已停止 {cfg.display_name}"

    await _run_and_reply(message, "停止", stopper())


@router.message(Command("switch"))
async def cmd_switch(message: Message) -> None:
    """处理 /switch 命令，停机后以新模型重启项目。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("用法: /switch <project> <model>")
        return
    project_raw, model = parts[1], parts[2]
    try:
        cfg = manager.require_project(project_raw)
    except ValueError as exc:
        await message.answer(str(exc))
        return

    async def switcher():
        """重新启动项目并切换到新的模型。"""

        await manager.stop_worker(cfg, update_state=True)
        chosen = await manager.run_worker(cfg, model=model)
        return f"已切换 {cfg.display_name} 至 {chosen}"

    await _run_and_reply(message, "切换", switcher())


@router.message(Command("authorize"))
async def cmd_authorize(message: Message) -> None:
    """处理 /authorize 命令，为项目登记 chat_id。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("用法: /authorize <project> <chat_id>")
        return
    project_raw, chat_raw = parts[1], parts[2]
    if not chat_raw.isdigit():
        await message.answer("chat_id 需要是数字")
        return
    chat_id = int(chat_raw)
    try:
        cfg = manager.require_project(project_raw)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    manager.update_chat_id(cfg.project_slug, chat_id)
    await message.answer(
        f"已记录 {cfg.display_name} 的 chat_id={chat_id}"
    )


@router.callback_query(F.data.startswith("project:wizard:skip:"))
async def on_project_wizard_skip(callback: CallbackQuery) -> None:
    """处理向导中的“跳过此项”按钮。"""

    if callback.message is None or callback.message.chat is None:
        return
    chat_id = callback.message.chat.id
    async with PROJECT_WIZARD_LOCK:
        session = PROJECT_WIZARD_SESSIONS.get(chat_id)
    if session is None:
        await callback.answer("当前没有进行中的项目流程。", show_alert=True)
        return
    if session.step_index >= len(session.fields):
        await callback.answer("当前流程已结束。", show_alert=True)
        return
    _, _, field = callback.data.partition("project:wizard:skip:")
    current_field = session.fields[session.step_index]
    if field != current_field:
        await callback.answer("当前步骤已变更，请按最新提示操作。", show_alert=True)
        return
    manager = await _ensure_manager()
    await callback.answer("已跳过")
    await _advance_wizard_session(
        session,
        manager,
        callback.message,
        "",
        prefix="已跳过 ✅",
    )


@router.message(F.text.in_(MASTER_MENU_BUTTON_ALLOWED_TEXTS))
async def on_master_projects_button(message: Message) -> None:
    """处理常驻键盘触发的项目概览请求。"""
    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    requested_text = message.text or ""
    reply_to_message_id: Optional[int] = message.message_id
    if requested_text != MASTER_MENU_BUTTON_TEXT:
        log.info(
            "收到旧版项目列表按钮，准备刷新聊天键盘",
            extra={"text": requested_text, "chat_id": message.chat.id},
        )
        await message.answer(
            "主菜单按钮已更新为“📂 项目列表”，当前会话已同步最新文案。",
            reply_markup=_build_master_main_keyboard(),
            reply_to_message_id=reply_to_message_id,
        )
        # 已推送最新键盘，后续回复无需继续引用原消息，避免重复引用提示
        reply_to_message_id = None
    await _send_projects_overview_to_chat(
        message.bot,
        message.chat.id,
        manager,
        reply_to_message_id=reply_to_message_id,
    )


@router.message(F.text.in_(MASTER_MANAGE_BUTTON_ALLOWED_TEXTS))
async def on_master_manage_button(message: Message) -> None:
    """处理常驻键盘的项目管理入口。"""
    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ 新增项目", callback_data="project:create:*"))
    model_name_map = dict(SWITCHABLE_MODELS)
    for cfg in manager.configs:
        state = manager.state_store.data.get(cfg.project_slug)
        current_model_value = state.model if state else cfg.default_model
        current_model_key = (current_model_value or "").lower()
        current_model_label = model_name_map.get(current_model_key, current_model_value or current_model_key or "-")
        builder.row(
            InlineKeyboardButton(
                text=f"⚙️ 管理 {cfg.display_name}",
                callback_data=f"project:manage:{cfg.project_slug}",
            ),
            InlineKeyboardButton(
                text=f"🧠 切换模型（当前模型 {current_model_label}）",
                callback_data=f"project:switch_prompt:{cfg.project_slug}",
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text="🔁 全部切换模型",
            callback_data="project:switch_all:*",
        )
    )
    builder.row(InlineKeyboardButton(text="📂 返回列表", callback_data="project:refresh:*"))
    markup = builder.as_markup()
    _ensure_numbered_markup(markup)
    await message.answer(
        "请选择要管理的项目，或点击“➕ 新增项目”创建新的 worker。",
        reply_markup=markup,
    )


@router.message()
async def cmd_fallback(message: Message) -> None:
    """兜底处理器：尝试继续向导，否则提示可用命令。"""

    _log_update(message)
    manager = await _ensure_manager()
    if not manager.is_authorized(message.chat.id):
        await message.answer("未授权。")
        return
    handled = await _handle_wizard_message(message, manager)
    if handled:
        return
    await message.answer("未识别的命令，请使用 /projects /run /stop /switch /authorize。")



def _delete_project_with_fallback(
    repository: ProjectRepository,
    *,
    stored_slug: str,
    original_slug: str,
    bot_name: str,
) -> Tuple[Optional[Exception], List[Tuple[str, Exception]]]:
    """尝试以多种标识删除项目，提升大小写与别名兼容性。"""

    attempts: List[Tuple[str, Exception]] = []

    def _attempt(candidate: str) -> Optional[Exception]:
        """实际执行删除，失败返回异常供后续兜底。"""
        slug = (candidate or "").strip()
        if not slug:
            return ValueError("slug 为空")
        try:
            repository.delete_project(slug)
        except ValueError as delete_exc:
            return delete_exc
        return None

    primary_error = _attempt(stored_slug)
    if primary_error is None:
        return None, attempts
    attempts.append((stored_slug, primary_error))

    if original_slug and original_slug != stored_slug:
        secondary_error = _attempt(original_slug)
        if secondary_error is None:
            return None, attempts
        attempts.append((original_slug, secondary_error))

    if bot_name:
        try:
            fallback_record = repository.get_by_bot_name(bot_name)
        except Exception as lookup_exc:
            attempts.append((f"bot:{bot_name}", lookup_exc))
        else:
            if fallback_record:
                fallback_slug = fallback_record.project_slug
                if not any(slug.lower() == fallback_slug.lower() for slug, _ in attempts):
                    fallback_error = _attempt(fallback_slug)
                    if fallback_error is None:
                        return None, attempts
                    attempts.append((fallback_slug, fallback_error))

    return primary_error, attempts


@router.callback_query(F.data.startswith("project:delete_confirm:"))
async def on_project_delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """处理删除确认按钮的回调逻辑。"""
    manager = await _ensure_manager()
    user_id = callback.from_user.id if callback.from_user else None
    if user_id is None or not manager.is_authorized(user_id):
        await callback.answer("未授权。", show_alert=True)
        return
    if callback.message is None:
        await callback.answer("无效操作", show_alert=True)
        return
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("无效操作", show_alert=True)
        return
    target_slug = parts[2]
    log.info(
        "删除确认回调: user=%s slug=%s",
        user_id,
        target_slug,
        extra={"project": target_slug},
    )
    current_state = await state.get_state()
    if current_state != ProjectDeleteStates.confirming.state:
        await callback.answer("确认流程已过期，请重新发起删除。", show_alert=True)
        return
    data = await state.get_data()
    stored_slug = str(data.get("project_slug", "")).strip()
    if stored_slug.lower() != target_slug.lower():
        await state.clear()
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.answer("确认信息已失效，请重新发起删除。", show_alert=True)
        return
    initiator_id = data.get("initiator_id")
    if initiator_id and initiator_id != user_id:
        await callback.answer("仅流程发起者可以确认删除。", show_alert=True)
        return
    expires_at = float(data.get("expires_at") or 0)
    if expires_at and time.time() > expires_at:
        await state.clear()
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.answer("确认已超时，请重新发起删除。", show_alert=True)
        return
    repository = _ensure_repository()
    original_slug = str(data.get("original_slug") or "").strip()
    bot_name = str(data.get("bot_name") or "").strip()
    error, attempts = _delete_project_with_fallback(
        repository,
        stored_slug=stored_slug,
        original_slug=original_slug,
        bot_name=bot_name,
    )
    if error is not None:
        log.error(
            "删除项目失败: %s",
            error,
            extra={
                "slug": stored_slug,
                "attempts": [slug for slug, _ in attempts],
            },
        )
        await callback.answer("删除失败，请稍后重试。", show_alert=True)
        await callback.message.answer(f"删除失败：{error}")
        return
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    _reload_manager_configs(manager)
    display_name = data.get("display_name") or stored_slug
    await callback.answer("项目已删除")
    await callback.message.answer(f"项目 {display_name} 已删除 ✅")
    await _send_projects_overview_to_chat(callback.message.bot, callback.message.chat.id, manager)


@router.callback_query(F.data == "project:delete_cancel")
async def on_project_delete_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """处理删除流程的取消按钮。"""
    manager = await _ensure_manager()
    user_id = callback.from_user.id if callback.from_user else None
    if user_id is None or not manager.is_authorized(user_id):
        await callback.answer("未授权。", show_alert=True)
        return
    if callback.message is None:
        await callback.answer("无效操作", show_alert=True)
        return
    current_state = await state.get_state()
    if current_state != ProjectDeleteStates.confirming.state:
        await callback.answer("当前没有待确认的删除流程。", show_alert=True)
        return
    data = await state.get_data()
    log.info(
        "删除取消回调: user=%s slug=%s",
        user_id,
        data.get("project_slug"),
    )
    initiator_id = data.get("initiator_id")
    if initiator_id and initiator_id != user_id:
        await callback.answer("仅流程发起者可以取消删除。", show_alert=True)
        return
    expires_at = float(data.get("expires_at") or 0)
    if expires_at and time.time() > expires_at:
        await state.clear()
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.answer("确认已超时，请重新发起删除。", show_alert=True)
        return
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    display_name = data.get("display_name") or data.get("project_slug") or ""
    await callback.answer("删除流程已取消")
    await callback.message.answer(f"已取消删除项目 {display_name}。")


@router.message(ProjectDeleteStates.confirming)
async def on_project_delete_text(message: Message, state: FSMContext) -> None:
    """兼容旧版交互，允许通过文本指令确认或取消删除。"""
    manager = await _ensure_manager()
    user = message.from_user
    if user is None or not manager.is_authorized(user.id):
        await message.answer("未授权。")
        return
    data = await state.get_data()
    initiator_id = data.get("initiator_id")
    if initiator_id and initiator_id != user.id:
        await message.answer("仅流程发起者可以继续此删除流程。")
        return
    expires_at = float(data.get("expires_at") or 0)
    if expires_at and time.time() > expires_at:
        await state.clear()
        prompt = getattr(message, "reply_to_message", None)
        if prompt:
            try:
                await prompt.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
        await message.answer("确认已超时，请重新发起删除。")
        return

    raw_text = (message.text or "").strip()
    if not raw_text:
        await message.answer("请使用按钮或输入“确认删除”/“取消”完成操作。")
        return
    normalized = raw_text.casefold().strip()
    normalized = normalized.rstrip("。.!？?")
    normalized_compact = normalized.replace(" ", "")
    confirm_tokens = {"确认删除", "确认", "confirm", "y", "yes"}
    cancel_tokens = {"取消", "cancel", "n", "no"}

    if normalized in cancel_tokens or normalized_compact in cancel_tokens:
        await state.clear()
        prompt = getattr(message, "reply_to_message", None)
        if prompt:
            try:
                await prompt.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
        display_name = data.get("display_name") or data.get("project_slug") or ""
        await message.answer(f"已取消删除项目 {display_name}。")
        return

    if not (
        normalized in confirm_tokens
        or normalized_compact in confirm_tokens
        or normalized.startswith("确认删除")
    ):
        await message.answer("请输入“确认删除”或通过按钮完成操作。")
        return

    stored_slug = str(data.get("project_slug", "")).strip()
    if not stored_slug:
        await state.clear()
        await message.answer("删除流程状态异常，请重新发起删除。")
        return
    original_slug = str(data.get("original_slug") or "").strip()
    bot_name = str(data.get("bot_name") or "").strip()
    repository = _ensure_repository()
    error, attempts = _delete_project_with_fallback(
        repository,
        stored_slug=stored_slug,
        original_slug=original_slug,
        bot_name=bot_name,
    )
    if error is not None:
        log.error(
            "删除项目失败(文本确认): %s",
            error,
            extra={
                "slug": stored_slug,
                "attempts": [slug for slug, _ in attempts],
            },
        )
        await message.answer(f"删除失败：{error}")
        return

    await state.clear()
    prompt = getattr(message, "reply_to_message", None)
    if prompt:
        try:
            await prompt.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
    _reload_manager_configs(manager)
    display_name = data.get("display_name") or stored_slug
    await message.answer(f"项目 {display_name} 已删除 ✅")
    await _send_projects_overview_to_chat(message.bot, message.chat.id, manager)



async def bootstrap_manager() -> MasterManager:
    """初始化项目仓库、状态存储与 manager，启动前清理旧 worker。"""

    load_env()
    tmux_prefix = os.environ.get("TMUX_SESSION_PREFIX", "vibe")
    _kill_existing_tmux(tmux_prefix)
    try:
        repository = ProjectRepository(CONFIG_DB_PATH, CONFIG_PATH)
    except Exception as exc:
        log.error("初始化项目仓库失败: %s", exc)
        sys.exit(1)

    records = repository.list_projects()
    if not records:
        log.warning("项目配置为空，将以空项目列表启动。")

    configs = [ProjectConfig.from_dict(record.to_dict()) for record in records]

    state_store = StateStore(STATE_PATH, {cfg.project_slug: cfg for cfg in configs})
    manager = MasterManager(configs, state_store=state_store)

    await manager.stop_all(update_state=True)
    log.info("已清理历史 tmux 会话，worker 需手动启动。")

    global MANAGER
    global PROJECT_REPOSITORY
    MANAGER = manager
    PROJECT_REPOSITORY = repository
    return manager


async def main() -> None:
    """master.py 的异步入口，完成 bot 启动与调度器绑定。"""

    manager = await bootstrap_manager()

    master_token = os.environ.get("MASTER_BOT_TOKEN")
    if not master_token:
        log.error("MASTER_BOT_TOKEN 未设置")
        sys.exit(1)

    proxy_url, proxy_auth, _ = _detect_proxy()
    session_kwargs = {}
    if proxy_url:
        session_kwargs["proxy"] = proxy_url
    if proxy_auth:
        session_kwargs["proxy_auth"] = proxy_auth
    session = AiohttpSession(**session_kwargs)
    bot = Bot(token=master_token, session=session)
    if proxy_url:
        session._connector_init.update({  # type: ignore[attr-defined]
            "family": __import__('socket').AF_INET,
            "ttl_dns_cache": 60,
        })
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.startup.register(_notify_restart_success)

    log.info("Master 已启动，监听管理员指令。")
    await _ensure_master_menu_button(bot)
    await _ensure_master_commands(bot)
    await _broadcast_master_keyboard(bot, manager)
    await dp.start_polling(bot)


if __name__ == "__main__":
    _terminate_other_master_processes()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Master 停止")
