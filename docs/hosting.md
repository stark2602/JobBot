# Free Hosting (GitHub Actions + Outlook)

This bot is a scheduled batch job. The $0 host is a GitHub Actions cron every 8 hours. SQLite + CSV persist via Actions cache (and optional commit). Email uses Outlook SMTP. Matching uses Gemini or Groq free tiers, or the offline heuristic backend.

**→ See [cmd.md](../cmd.md) for complete deployment commands and alternatives (Windows Task Scheduler, Docker, VMs).**

## 1. Put the repo on GitHub

Create a public or private repo and push this project.

## 2. GitHub secrets

Repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `JOBBOT_SMTP_USER` | your Outlook / Microsoft 365 address |
| `JOBBOT_SMTP_PASSWORD` | [Outlook app password](https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944) (not your login password) |
| `JOBBOT_DIGEST_TO` | inbox that should receive the digest |
| `JOBBOT_LLM_API_KEY` | optional; [Google AI Studio](https://aistudio.google.com/apikey) or [Groq](https://console.groq.com/keys) free key |

## 3. Outlook SMTP

- Host: `smtp.office365.com` (or `smtp-mail.outlook.com`)
- Port: `587` STARTTLS
- Enable 2FA and create an app password if the account requires it

## 4. Workflow

`.github/workflows/jobbot.yml` runs at `0 */8 * * *` UTC and on `workflow_dispatch`.

It:

1. Installs deps
2. Restores `data/jobs.sqlite` from cache (dedupe across runs)
3. Runs `python -m agent.cli --root .`
4. Uploads `data/jobs.csv` as an artifact
5. Saves the SQLite cache

## 5. Matcher without a paid API

- `JOBBOT_MATCHER_BACKEND=heuristic` — $0, no key, keyword overlap
- `JOBBOT_MATCHER_BACKEND=llm` + Gemini Flash or Groq — $0 within free quotas

## 6. Local cron alternative

Windows Task Scheduler every 8 hours:

```
python -m agent.cli --root C:\path\to\agent
```

## 7. Docker on a free VM (optional)

Oracle Cloud / Fly.io free tiers can run `docker compose up` with the same env vars. GitHub Actions is the path with no VM to babysit.
