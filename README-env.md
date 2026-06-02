# README-env

Environment-specific operations note for the active PITH v5 deployment on `msk-1-vm-ngf0`.

This file is an operational runbook for the current VM.
It is not the main project overview.

For system and product documentation, see:
- `README.md`
- `docs/PITH_DOCS_INDEX.md`
- `docs/PITH_MASTER_PLAN.md`

---

## Active environment

Host:
- `msk-1-vm-ngf0`

Primary runtime path:
- `/root/pith_v5`

Primary live config:
- `/root/pith_v5/config.yaml`

Rule:
- backup configs inside the repo are recovery references only;
- `/root/pith_v5/config.yaml` is the live runtime source of truth.

---

## Core services

Primary systemd units for the active environment:

- `pith_v5.service` — main PITH v5 Telegram runtime
- `pith-dashboard.service` — dashboard service when enabled

---

## Legacy or auxiliary units

These units should be treated as legacy, alternate, or normally disabled unless intentionally reactivated:

- `pith.service`
- `pith-bot.service`
- `pith-v5.service`
- `pithv5.service`
- `pith_daily_report.service`

---

## Config operations

After changing `config.yaml`:

1. Validate YAML syntax.

```bash
cd /root/pith_v5
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

2. Restart the runtime.

```bash
systemctl restart pith_v5.service
```

3. Check service health.

```bash
systemctl status pith_v5.service --no-pager
```

4. Check recent logs if anything looks wrong.

```bash
journalctl -u pith_v5.service -n 50 --no-pager
```

---

## Runtime verification

Useful Telegram control questions after restart or config changes:

- `Где лежит config.yaml?`
- `Какая модель используется сейчас?`
- `Покажи system prompt`
- `Посмотри логи сервиса`

These checks help confirm that the live runtime is using the expected config and still exposes planner, model, governance, and error surfaces correctly.

---

## Operations quick start

```bash
cd /root/pith_v5
source /root/pith_v5/venv/bin/activate
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
systemctl restart pith_v5.service
systemctl status pith_v5.service --no-pager
journalctl -u pith_v5.service -n 50 --no-pager
```

---

## Current verified state

Verified on `2026-05-22`:

- `systemctl is-active pith_v5.service` → `active`
- `systemctl is-enabled pith_v5.service` → `enabled`

Last verified smoke path:
- YAML config validated
- service restarted cleanly
- Telegram runtime responded
- tasks and traces were produced

---

## Related ops docs

- `docs/observability-smoke-checklist.md` — deploy and smoke validation checklist
- `PITH_CHANGELOG.md` — meaningful runtime and config changes
- `PITH_ACTIVE_CONTEXT.md` — current operational phase and priorities
- `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md` — tool/runtime safety policy