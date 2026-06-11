#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
PID_FILE="$ROOT_DIR/tmp/xrwl-server.pid"
LOG_FILE="$ROOT_DIR/tmp/xrwl-server.log"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"

usage() {
  cat <<USAGE
Usage: scripts/start.sh [start|stop|restart|status]

Environment:
  HOST        Bind address, default: 127.0.0.1
  PORT        Bind port, default: 8000
  PYTHON_BIN  Python executable, default: python3
  NODE_BIN    Node executable for optional JS syntax check, default: node
USAGE
}

log() {
  printf '[xrwl] %s\n' "$*"
}

fail() {
  printf '[xrwl] ERROR: %s\n' "$*" >&2
  exit 1
}

pid_running() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

pid_from_file() {
  [[ -f "$PID_FILE" ]] && sed -n '1p' "$PID_FILE"
}

pids_on_port() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true
  fi
}

stop_pid() {
  local pid="$1"
  if ! pid_running "$pid"; then
    return
  fi

  log "Stopping process $pid"
  kill "$pid" 2>/dev/null || true
  for _ in {1..20}; do
    if ! pid_running "$pid"; then
      return
    fi
    sleep 0.2
  done

  log "Process $pid did not exit, forcing stop"
  kill -9 "$pid" 2>/dev/null || true
}

stop_server() {
  local pid
  pid="$(pid_from_file || true)"
  if [[ -n "${pid:-}" ]]; then
    stop_pid "$pid"
  fi

  while IFS= read -r port_pid; do
    [[ -n "$port_pid" ]] && stop_pid "$port_pid"
  done < <(pids_on_port)

  rm -f "$PID_FILE"
}

check_dependencies() {
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python is not installed or PYTHON_BIN is invalid: $PYTHON_BIN"
  "$PYTHON_BIN" - <<'PY'
import sqlite3
import sys
print(f"Python {sys.version.split()[0]} OK, sqlite3 OK")
PY

  if command -v lsof >/dev/null 2>&1; then
    log "Port process detection OK"
  else
    log "lsof not found; only PID-file managed processes can be stopped"
  fi

  if command -v "$NODE_BIN" >/dev/null 2>&1; then
    "$NODE_BIN" --check "$ROOT_DIR/frontend/src/app.js" >/dev/null
    log "Node syntax check OK"
  else
    log "Node not found; skipped optional frontend syntax check"
  fi
}

initialize_data() {
  "$PYTHON_BIN" "$ROOT_DIR/scripts/init_db.py"
}

start_server() {
  mkdir -p "$(dirname "$PID_FILE")"
  stop_server
  check_dependencies
  initialize_data

  log "Starting server at http://$HOST:$PORT"
  : >"$LOG_FILE"
  nohup env HOST="$HOST" PORT="$PORT" PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/xrwl-pycache}" \
    "$PYTHON_BIN" "$ROOT_DIR/backend/server.py" >>"$LOG_FILE" 2>&1 &
  local pid="$!"
  echo "$pid" >"$PID_FILE"

  wait_for_server "$pid"

  log "Started process $pid"
  log "Log file: $LOG_FILE"
}

wait_for_server() {
  local pid="$1"
  local url="http://$HOST:$PORT/"
  for _ in {1..30}; do
    if ! pid_running "$pid"; then
      rm -f "$PID_FILE"
      tail -n 40 "$LOG_FILE" >&2 || true
      fail "Server failed to start"
    fi
    if "$PYTHON_BIN" - "$url" >/dev/null 2>&1 <<'PY'
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=0.3) as response:
    if 200 <= response.status < 500:
        sys.exit(0)
sys.exit(1)
PY
    then
      return
    fi
    sleep 0.2
  done

  tail -n 40 "$LOG_FILE" >&2 || true
  fail "Server did not become ready at $url"
}

server_status() {
  local pid
  pid="$(pid_from_file || true)"
  if [[ -n "${pid:-}" ]] && pid_running "$pid"; then
    log "Running at http://$HOST:$PORT (pid $pid)"
    return
  fi

  local found=""
  found="$(pids_on_port | paste -sd ',' - 2>/dev/null || true)"
  if [[ -n "$found" ]]; then
    log "Port $PORT is in use by pid(s): $found"
  else
    log "Not running"
  fi
}

main() {
  cd "$ROOT_DIR"
  case "${1:-start}" in
    start)
      start_server
      ;;
    stop)
      stop_server
      log "Stopped"
      ;;
    restart)
      start_server
      ;;
    status)
      server_status
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      usage
      exit 2
      ;;
  esac
}

main "$@"
