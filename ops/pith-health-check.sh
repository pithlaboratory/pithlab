#!/usr/bin/env bash
set -euo pipefail

HOST="$(hostname)"
LOG_FILE="/var/log/pith-health.log"
STATE_DIR="/var/run/pith-health"
BOT_SERVICE="pith_v5.service"
DASH_SERVICE="pith-dashboard.service"
DASH_URL="http://127.0.0.1:8501/_stcore/health"
TG_TOKEN="${TG_TOKEN:-}"
OWNER_CHAT_ID="${OWNER_CHAT_ID:-}"
COOLDOWN_SECONDS=600
HAS_ISSUES=0

mkdir -p "$STATE_DIR"

log() {
  echo "$(date '+%F %T') $1" >> "$LOG_FILE"
}

should_send_alert() {
  local key="$1"
  local state_file="${STATE_DIR}/${key}.state"
  local now ts

  now=$(date +%s)
  ts=0

  if [[ -f "$state_file" ]]; then
    ts=$(cat "$state_file" 2>/dev/null || echo 0)
  fi

  if (( now - ts < COOLDOWN_SECONDS )); then
    return 1
  fi

  echo "$now" > "$state_file"
  return 0
}

send_alert() {
  local key="$1"
  local text="$2"

  if ! should_send_alert "$key"; then
    log "SKIP_ALERT (cooldown): $text"
    return 0
  fi

  log "ALERT: $text"

  if [[ -n "$TG_TOKEN" && -n "$OWNER_CHAT_ID" ]]; then
    curl -fsS -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
      -d chat_id="$OWNER_CHAT_ID" \
      --data-urlencode text="[$HOST] $text" >/dev/null || true
  fi
}

check_service() {
  local svc="$1"
  local key="svc_${svc}"

  if ! systemctl is-active --quiet "$svc"; then
    send_alert "$key" "$svc is DOWN"
    HAS_ISSUES=1
    return 0
  fi

  log "OK: $svc active"
}

check_http() {
  local url="$1"
  local name="$2"
  local key="http_${name}"
  local code

  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 8 "$url" || true)

  if [[ "$code" != "200" && "$code" != "302" && "$code" != "403" ]]; then
    send_alert "$key" "$name HTTP check failed: $url returned $code"
    HAS_ISSUES=1
    return 0
  fi

  log "OK: $name HTTP $code"
}

check_service "$BOT_SERVICE"
check_service "$DASH_SERVICE"
check_http "$DASH_URL" "pith-dashboard health"

if [[ "$HAS_ISSUES" -eq 1 ]]; then
  log "SUMMARY: issues detected"
else
  log "SUMMARY: all checks passed"
fi

exit 0

