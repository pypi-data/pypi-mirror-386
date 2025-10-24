#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="$ROOT_DIR/state/master_restart.lock"
START_LOG="$ROOT_DIR/logs/start.log"
CODEX_STAMP_FILE="$ROOT_DIR/state/npm_codex_install.stamp"
CODEX_INSTALL_TTL="${CODEX_INSTALL_TTL:-86400}"

log_line() {
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S%z')
  printf '[%s] %s\n' "$ts" "$*"
}

log_info() {
  log_line "$@"
}

log_error() {
  log_line "$@" >&2
}

cleanup() {
  rm -f "$LOCK_FILE"
}

trap cleanup EXIT

cd "$ROOT_DIR"

mkdir -p "$(dirname "$LOCK_FILE")"
mkdir -p "$(dirname "$START_LOG")"
touch "$START_LOG"
exec >>"$START_LOG"
exec 2>&1

log_info "start.sh 启动，pid=$$"

if [[ -f "$LOCK_FILE" ]]; then
  log_error "已有 start.sh 在执行，跳过本次启动。"
  exit 1
fi

printf '%d\n' $$ > "$LOCK_FILE"

log_info "锁文件已创建：$LOCK_FILE"

ensure_codex_installed() {
  local need_install=1
  local now
  local codex_bin
  if ! command -v npm >/dev/null 2>&1; then
    log_error "未检测到 npm，可执行文件缺失，跳过 @openai/codex 全局安装"
    return
  fi

  log_info "检测到 npm 版本：$(npm --version)"

  if [[ ! "$CODEX_INSTALL_TTL" =~ ^[0-9]+$ ]]; then
    log_error "CODEX_INSTALL_TTL 非法值：$CODEX_INSTALL_TTL，回退为 86400 秒"
    CODEX_INSTALL_TTL=86400
  fi

  if (( need_install )); then
    codex_bin=$(command -v codex 2>/dev/null || true)
    if [[ -n "$codex_bin" ]]; then
      log_info "Detected existing codex binary at ${codex_bin}; skipping install (upgrade manually if needed)"
      need_install=0
    elif [[ -x "/opt/homebrew/bin/codex" ]]; then
      log_info "Detected existing codex binary at /opt/homebrew/bin/codex; skipping install (upgrade manually if needed)"
      need_install=0
    fi
  fi

  if (( need_install )) && [[ -f "$CODEX_STAMP_FILE" ]]; then
    local last_ts
    last_ts=$(cat "$CODEX_STAMP_FILE" 2>/dev/null || printf '0')
    if [[ "$last_ts" =~ ^[0-9]+$ ]]; then
      now=$(date +%s)
      local elapsed=$(( now - last_ts ))
      if (( elapsed < CODEX_INSTALL_TTL )); then
        local remaining=$(( CODEX_INSTALL_TTL - elapsed ))
        log_info "Previous install happened ${elapsed}s ago (cooldown ${CODEX_INSTALL_TTL}s); skipping install with ${remaining}s remaining"
        need_install=0
      fi
    fi
  fi

  if (( need_install )); then
    log_info "开始执行 npm install -g @openai/codex@latest"
    if npm install -g @openai/codex@latest; then
      now=$(date +%s)
      printf '%s\n' "$now" > "$CODEX_STAMP_FILE"
      log_info "npm install -g @openai/codex@latest 成功"
    else
      local status=$?
      log_error "npm install -g @openai/codex@latest failed (exit code ${status}); continuing startup"
    fi
  fi
}

ensure_codex_installed

select_python_binary() {
  # 选择满足 CPython <=3.13 的解释器，避免 PyO3 依赖构建失败
  local candidates=()
  local chosen=""
  local name
  if [[ -n "${VIBEGO_PYTHON:-}" ]]; then
    candidates+=("$VIBEGO_PYTHON")
  fi
  for name in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
    if [[ "${VIBEGO_PYTHON:-}" == "$name" ]]; then
      continue
    fi
    candidates+=("$name")
  done

  for name in "${candidates[@]}"; do
    if [[ -z "$name" ]]; then
      continue
    fi
    if ! command -v "$name" >/dev/null 2>&1; then
      continue
    fi
    local version_raw
    version_raw=$("$name" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null) || continue
    local major="${version_raw%%.*}"
    local minor="${version_raw#*.}"
    if [[ "$major" != "3" ]]; then
      log_info "跳过 ${name} (版本 ${version_raw})：非 CPython 3.x"
      continue
    fi
    if [[ "$minor" =~ ^[0-9]+$ ]] && (( minor > 13 )); then
      log_info "跳过 ${name} (版本 ${version_raw})：高于 3.13"
      continue
    fi
    if [[ "$minor" =~ ^[0-9]+$ ]] && (( minor < 9 )); then
      log_info "跳过 ${name} (版本 ${version_raw})：低于 3.9，可能缺少官方轮子"
      continue
    fi
    chosen="$name"
    log_info "使用 Python 解释器：${chosen} (版本 ${version_raw})"
    break
  done

  if [[ -z "$chosen" ]]; then
    log_error "未找到满足 <=3.13 的 Python 解释器，可通过设置 VIBEGO_PYTHON 指定路径"
    exit 1
  fi

  printf '%s' "$chosen"
}

# 检查Python依赖是否已安装完整
check_deps_installed() {
  # 检查虚拟环境是否存在
  if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    log_info "虚拟环境不存在，需要初始化"
    return 1
  fi

  # 检查虚拟环境的Python解释器
  if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
    log_info "虚拟环境Python解释器缺失"
    return 1
  fi

  # 激活虚拟环境并检查关键依赖包
  # aiogram: Telegram Bot框架
  # aiohttp: 异步HTTP客户端
  # aiosqlite: 异步SQLite数据库
  if ! "$ROOT_DIR/.venv/bin/python" -c "import aiogram, aiohttp, aiosqlite" 2>/dev/null; then
    log_info "关键依赖包缺失或损坏"
    return 1
  fi

  log_info "依赖检查通过，虚拟环境完整"
  return 0
}

if pgrep -f "python.*master.py" >/dev/null 2>&1; then
  log_info "检测到历史 master 实例，正在终止..."
  pkill -f "python.*master.py" || true
  sleep 1
  if pgrep -f "python.*master.py" >/dev/null 2>&1; then
    log_info "残留 master 进程仍在，执行强制结束"
    pkill -9 -f "python.*master.py" || true
    sleep 1
  fi
  if pgrep -f "python.*master.py" >/dev/null 2>&1; then
    log_error "仍存在 master 进程，请手动检查后再启动"
    exit 1
  fi
  log_info "历史 master 实例已清理"
fi

# 智能依赖管理：仅在必要时安装
REQUIREMENTS_FILE="${VIBEGO_REQUIREMENTS_PATH:-$ROOT_DIR/scripts/requirements.txt}"
if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  log_error "依赖文件缺失: $REQUIREMENTS_FILE"
  exit 1
fi

PYTHON_BIN="$(select_python_binary)"

# 检查是否需要安装依赖
if check_deps_installed; then
  log_info "依赖已安装且完整，跳过pip install（加速重启）"
  source .venv/bin/activate
else
  log_info "首次启动或依赖缺失，正在安装依赖..."

  # 创建或重建虚拟环境
  "$PYTHON_BIN" -m venv .venv
  source .venv/bin/activate

  # 安装依赖
  log_info "开始执行 pip install -r $REQUIREMENTS_FILE"
  pip install -r "$REQUIREMENTS_FILE"
  log_info "依赖安装完成"
fi

# 后台启动 master，日志落在 vibe.log
# 显式传递重启标记环境变量（如果存在）
if [[ -n "${MASTER_RESTART_EXPECTED:-}" ]]; then
  log_info "检测到重启标记环境变量 MASTER_RESTART_EXPECTED=$MASTER_RESTART_EXPECTED"
  export MASTER_RESTART_EXPECTED
fi

log_info "准备启动 master 进程..."
nohup python master.py >> /dev/null 2>&1 &
MASTER_PID=$!
log_info "master 已后台启动，PID=$MASTER_PID，日志写入 vibe.log"

# 健康检查：等待 master 上线并验证关键 worker
log_info "开始执行健康检查..."
HEALTHCHECK_START=$(date +%s)

if python scripts/master_healthcheck.py --project hyphavibebotbackend; then
  HEALTHCHECK_END=$(date +%s)
  HEALTHCHECK_DURATION=$((HEALTHCHECK_END - HEALTHCHECK_START))
  log_info "✅ master 健康检查通过，耗时 ${HEALTHCHECK_DURATION}s"
else
  HEALTHCHECK_END=$(date +%s)
  HEALTHCHECK_DURATION=$((HEALTHCHECK_END - HEALTHCHECK_START))
  log_error "⚠️ master 健康检查失败，耗时 ${HEALTHCHECK_DURATION}s"
  log_error "建议检查："
  log_error "  - 进程状态: ps aux | grep 'python.*master.py'"
  log_error "  - 启动日志: tail -100 $ROOT_DIR/logs/start.log"
  log_error "  - 运行日志: tail -100 $ROOT_DIR/vibe.log"
  log_error "  - 进程 PID: $MASTER_PID"

  # 检查进程是否仍在运行
  if kill -0 "$MASTER_PID" 2>/dev/null; then
    log_info "master 进程仍在运行（PID=$MASTER_PID），允许继续启动"
    log_info "⚠️ 请手动验证服务是否正常工作"
  else
    log_error "❌ master 进程已退出，启动失败"
    exit 1
  fi
fi
