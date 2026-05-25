# PITH v5 Environment

This document describes the current deployment environment for PITH on `msk-1-vm-ngf0` and should be treated as the environment-specific operations note for the active VM. [file:278]

For project-level overview and system documentation, see:

- `README.md`
- `docs/PITH_SYSTEM_VISION.md`
- `docs/PITH_CAPABILITIES_MODEL.md`
- `docs/PITH_OPERATING_STANDARD.md`
- `docs/PITH_MASTER_PLAN.md`

## Core services

The following systemd units are the primary services for the active environment:

- `pith_v5.service` — main PITH v5 Telegram runtime; runs from `/root/pith_v5` and uses `/root/pith_v5/config.yaml` as the primary runtime config source. [file:278]
- `pith-dashboard.service` — Streamlit dashboard service when the dashboard surface is enabled from the same repo or deployed path. [file:278]

## Legacy or auxiliary units

The following units should be treated as legacy, alternate, or normally disabled unless intentionally reactivated:

- `pith.service`
- `pith-bot.service`
- `pith-v5.service`
- `pithv5.service`
- `pith_daily_report.service`

## Config

- Main runtime config: `/root/pith_v5/config.yaml`. [file:278]
- Backup configs inside the repo should be treated as recovery references, not as live sources of truth. [file:278]

## Operational checklist

After changing `config.yaml`:

1. Validate YAML syntax.

```bash
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

## Runtime verification

Useful control questions in Telegram after restart or config changes:

- `Где лежит config.yaml?`
- `Какая модель используется сейчас?`
- `Покажи system prompt`
- `Посмотри логи сервиса`

These prompts are useful because the active Telegram runtime already exposes model access, planner behavior, governance paths, feedback handling, and runtime error surfaces through the main interface. [file:278]

## Current verified state

Verified on `2026-05-22`:

- `systemctl is-active pith_v5.service` → `active`
- `systemctl is-enabled pith_v5.service` → `enabled`
- Last restart and smoke checks passed:
  - YAML config validated
  - service restarted cleanly
  - Telegram runtime responded and produced tasks and traces

## Related docs

- `README.md` — top-level project overview.
- `docs/PITH_SYSTEM_VISION.md` — system and product direction.
- `docs/PITH_CAPABILITIES_MODEL.md` — capability model.
- `docs/PITH_OPERATING_STANDARD.md` — operating standard.
- `docs/PITH_MASTER_PLAN.md` — roadmap order, milestones, and implementation sequencing.
- `docs/observability-smoke-checklist.md` — deploy and smoke validation checklist. [file:278]