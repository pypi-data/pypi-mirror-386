#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/scripts/models"
LOG_ROOT="${LOG_ROOT:-$ROOT_DIR/logs}"
MODEL_DEFAULT="${MODEL_DEFAULT:-codex}"
PROJECT_DEFAULT="${PROJECT_NAME:-}"

usage() {
  cat <<USAGE
用法：${0##*/} [--model 名称] [--project 名称]
  --model    目标模型，默认 $MODEL_DEFAULT
  --project  项目别名；未指定时尝试使用当前目录配置
USAGE
}

MODEL="$MODEL_DEFAULT"
PROJECT_OVERRIDE="$PROJECT_DEFAULT"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"; shift 2 ;;
    --project)
      PROJECT_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "未知参数: $1" >&2
      usage
      exit 1 ;;
  esac
done

# shellcheck disable=SC1090
source "$MODELS_DIR/common.sh"

MODEL_SCRIPT="$MODELS_DIR/$MODEL.sh"
if [[ -f "$MODEL_SCRIPT" ]]; then
  # shellcheck disable=SC1090
  source "$MODEL_SCRIPT"
  if declare -f model_configure >/dev/null 2>&1; then
    model_configure
  fi
fi

POINTER_BASENAME="${MODEL_POINTER_BASENAME:-current_session.txt}"

kill_tty_sessions() {
  local session="$1"
  if command -v tmux >/dev/null 2>&1 && tmux -u has-session -t "$session" >/dev/null 2>&1; then
    tmux -u kill-session -t "$session" >/dev/null 2>&1 || true
  fi
}

clear_session_files() {
  local log_dir="$1"
  rm -f "$log_dir/$POINTER_BASENAME"
}

kill_pid_file() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    local fallback_dir
    fallback_dir="$(dirname "$pid_file")"
    [[ -d "$fallback_dir" ]] && clear_session_files "$fallback_dir"
    return
  fi
  local bot_pid
  bot_pid=$(cat "$pid_file")
  if [[ -n "$bot_pid" ]] && ps -p "$bot_pid" >/dev/null 2>&1; then
    kill "$bot_pid" >/dev/null 2>&1 || true
    sleep 0.5
    if ps -p "$bot_pid" >/dev/null 2>&1; then
      kill -9 "$bot_pid" >/dev/null 2>&1 || true
    fi
  fi
  rm -f "$pid_file"
  local pid_dir
  pid_dir="$(dirname "$pid_file")"
  [[ -d "$pid_dir" ]] && clear_session_files "$pid_dir"
}

stop_single_worker() {
  local project_name="$1" model_name="$2"
  local log_dir pid_file tmux_session
  log_dir="$(log_dir_for "$model_name" "$project_name")"
  pid_file="$log_dir/bot.pid"
  tmux_session="$(tmux_session_for "$project_name")"
  kill_tty_sessions "$tmux_session"
  kill_pid_file "$pid_file"
  clear_session_files "$log_dir"
}

stop_all_workers() {
  local stopped=0
  if command -v tmux >/dev/null 2>&1; then
    local prefix="$TMUX_SESSION_PREFIX"
    [[ -z "$prefix" ]] && prefix="vibe"
    local full_prefix
    if [[ "$prefix" == *- ]]; then
      full_prefix="$prefix"
    else
      full_prefix="${prefix}-"
    fi
    local sessions
    sessions=$(tmux -u list-sessions 2>/dev/null | awk -F: -v prefix="$full_prefix" '$1 ~ "^" prefix {print $1}')
    if [[ -n "$sessions" ]]; then
      while IFS= read -r sess; do
        [[ -z "$sess" ]] && continue
        tmux -u kill-session -t "$sess" >/dev/null 2>&1 || true
        stopped=1
      done <<<"$sessions"
    fi
  fi

  if [[ -d "$LOG_ROOT" ]]; then
    while IFS= read -r pid_file; do
      [[ -z "$pid_file" ]] && continue
      kill_pid_file "$pid_file"
      stopped=1
    done < <(find "$LOG_ROOT" -maxdepth 4 -type f -name "bot.pid" 2>/dev/null)
  fi
  return $stopped
}

if [[ -n "$PROJECT_OVERRIDE" ]]; then
  PROJECT_NAME="$(sanitize_slug "$PROJECT_OVERRIDE")"
  stop_single_worker "$PROJECT_NAME" "$MODEL"
else
  if ! stop_all_workers; then
    # fallback:默认 project 名称
    stop_single_worker "project" "$MODEL"
  fi
fi

# 已通过 pid 文件与 tmux 会话按项目停止进程，无需额外全局 pkill，避免误杀其它项目

exit 0
