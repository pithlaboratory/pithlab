# Pith v5 — msk-1-vm-ngf0 Environment

## Core services (systemd)

- pith_v5.service — Pith v5 Telegram Bot (боевой)
  - Runs from: /root/pith_v5
  - Config:    /root/pith_v5/config.yaml
- pith-dashboard.service — Pith Streamlit Dashboard (боевой)
  - Runs from: /root/pith_v5 (или фактический путь, если другой)

## Legacy / auxiliary units

- pith.service, pith-bot.service, pith-v5.service, pithv5.service — старые / альтернативные юниты, отключены.
- pith_daily_report.service — планировщик отчёта, статический, не активен.

## Config

- Main config: /root/pith_v5/config.yaml
- Backups:
  - config.yaml.bak             — предыдущая версия (до 2026-05-20)
  - config.yaml.good-2026-05-20 — проверенный рабочий baseline

## Operational checklist

- После изменения config.yaml:
  1) python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
  2) systemctl restart pith_v5.service
  3) systemctl status pith_v5.service --no-pager

- Контрольные вопросы в Telegram:
  - "Где лежит config.yaml?"
  - "Какая модель используется сейчас?"
  - "Покажи system prompt"
  - "Посмотри логи сервиса"
