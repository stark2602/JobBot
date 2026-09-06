# Infra

Free host is GitHub Actions (`docs/hosting.md`). No Terraform — no cloud account required.

Images: `infra/Dockerfile`. Compose: `docker-compose.yml` (SQLite volume only).

Env files: `infra/config/{local,staging,production}.yaml` document matcher/SMTP defaults; runtime still loads `.env` via `agent.config.load_config`.
