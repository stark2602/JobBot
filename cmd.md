# Hosting Commands & Deployment Guide

Complete command reference to host JobBot on GitHub Actions, Windows Task Scheduler, Docker, or a free VM.

---

## Option 1: GitHub Actions (Recommended — $0, Zero Maintenance)

### Step 1: Create GitHub repo

```bash
git init
git add .
git commit -m "Initial JobBot commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/jobbot.git
git push -u origin main
```

### Step 2: Add GitHub Secrets

In your GitHub repo, go to **Settings → Secrets and variables → Actions** and add:

```bash
JOBBOT_SMTP_USER=your-outlook@outlook.com
JOBBOT_SMTP_PASSWORD=your-16-char-app-password
JOBBOT_DIGEST_TO=recipient@outlook.com
JOBBOT_LLM_API_KEY=your-gemini-or-groq-key  # Optional
JOBBOT_MATCHER_BACKEND=heuristic  # or "llm"
JOBBOT_LLM_PROVIDER=gemini  # or "groq"
```

### Step 3: Create workflow file

Create `.github/workflows/jobbot.yml`:

```yaml
name: JobBot Fresher Search

on:
  schedule:
    - cron: "0 */8 * * *"  # Run every 8 hours UTC
  workflow_dispatch:       # Manual trigger button

jobs:
  search:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Restore SQLite cache (dedup DB)
        uses: actions/cache@v3
        with:
          path: data/jobs.sqlite
          key: jobbot-sqlite-${{ runner.os }}
          restore-keys: jobbot-sqlite-

      - name: Run JobBot
        env:
          JOBBOT_MATCHER_BACKEND: ${{ secrets.JOBBOT_MATCHER_BACKEND || 'heuristic' }}
          JOBBOT_LLM_PROVIDER: ${{ secrets.JOBBOT_LLM_PROVIDER || 'gemini' }}
          JOBBOT_LLM_MODEL: gemini-2.0-flash
          JOBBOT_LLM_API_KEY: ${{ secrets.JOBBOT_LLM_API_KEY || '' }}
          JOBBOT_SEND_EMAIL: "true"
          JOBBOT_SMTP_USER: ${{ secrets.JOBBOT_SMTP_USER }}
          JOBBOT_SMTP_PASSWORD: ${{ secrets.JOBBOT_SMTP_PASSWORD }}
          JOBBOT_SMTP_HOST: smtp.office365.com
          JOBBOT_SMTP_PORT: "587"
          JOBBOT_DIGEST_TO: ${{ secrets.JOBBOT_DIGEST_TO }}
          JOBBOT_AUTO_CONFIRM_EMAIL: "true"
        run: python -m agent.cli --root .

      - name: Upload jobs CSV as artifact
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: jobs-${{ github.run_number }}
          path: data/jobs.csv
          retention-days: 30

      - name: Commit CSV to repo (optional)
        if: always()
        run: |
          git config --global user.name "jobbot[bot]"
          git config --global user.email "bot@jobbot.local"
          git add data/jobs.csv
          git commit -m "Update jobs.csv - run ${{ github.run_number }}" || true
          git push
```

### Step 4: First run (manual)

Go to **Actions → JobBot Fresher Search → Run workflow → Run workflow**

Check the logs for success/failure.

### Step 5: Monitor

- Emails arrive in `JOBBOT_DIGEST_TO` every 8 hours
- Download CSVs from **Actions → Latest run → Artifacts**
- Re-run anytime from the **Run workflow** button

**Zero cost.** GitHub Actions free tier: 2,000 minutes/month (this job uses ~30s/run).

---

## Option 2: Windows Task Scheduler (Local)

### Step 1: Create batch file

Save as `C:\Users\mps26\Downloads\agent\jobbot.bat`:

```batch
@echo off
cd C:\Users\mps26\Downloads\agent
call .\.venv\Scripts\Activate.ps1
set JOBBOT_MATCHER_BACKEND=heuristic
set JOBBOT_SEND_EMAIL=false
python -m agent.cli --root .
echo Run complete. Results saved to data/jobs.csv
pause
```

### Step 2: Create PowerShell wrapper (for scheduled task)

Save as `C:\Users\mps26\Downloads\agent\jobbot-task.ps1`:

```powershell
# Set environment
$env:JOBBOT_MATCHER_BACKEND = "heuristic"
$env:JOBBOT_SEND_EMAIL = "false"

# Or enable email:
# $env:JOBBOT_SEND_EMAIL = "true"
# $env:JOBBOT_SMTP_USER = "your-outlook@outlook.com"
# $env:JOBBOT_SMTP_PASSWORD = "app-password"
# $env:JOBBOT_DIGEST_TO = "recipient@outlook.com"

# Run
$venv = "C:\Users\mps26\Downloads\agent\.venv\Scripts\Activate.ps1"
& $venv
python -m agent.cli --root C:\Users\mps26\Downloads\agent
```

### Step 3: Register scheduled task

Open PowerShell as **Administrator** and run:

```powershell
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 8) -RepeatIndefinitely -At (Get-Date)
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Users\mps26\Downloads\agent\jobbot-task.ps1"
Register-ScheduledTask `
  -TaskName "JobBot-Fresher-Search" `
  -Trigger $trigger `
  -Action $action `
  -RunLevel Highest `
  -Description "JobBot fresher job search every 8 hours"
```

### Step 4: Verify

```powershell
Get-ScheduledTask -TaskName "JobBot-Fresher-Search"
```

Output: `Status = Ready` ✓

### Step 5: Manual test run

```powershell
Start-ScheduledTask -TaskName "JobBot-Fresher-Search"
Get-ScheduledTaskInfo -TaskName "JobBot-Fresher-Search"
```

### Step 6: View logs

```powershell
# Event Viewer: Windows Logs → Application (search "JobBot")
Get-EventLog -LogName Application -Source TaskScheduler -Newest 10
```

---

## Option 3: Docker on Free VM

### Step 1: Create Dockerfile

Already included: `infra/Dockerfile`

Build:

```bash
docker build -f infra/Dockerfile -t jobbot .
```

### Step 2: Run locally

```bash
docker run --rm \
  -e JOBBOT_MATCHER_BACKEND=heuristic \
  -e JOBBOT_SEND_EMAIL=false \
  -v $(pwd)/data:/app/data \
  jobbot
```

### Step 3: Deploy to free tier VM

#### Fly.io (free tier)

```bash
# Install flyctl
# https://fly.io/docs/getting-started/installing-flyctl/

# Initialize Fly app
flyctl launch --name jobbot-fresher

# Configure env in fly.toml:
# [env]
# JOBBOT_MATCHER_BACKEND = "heuristic"
# JOBBOT_SEND_EMAIL = "false"

# Deploy
flyctl deploy

# Run on schedule (requires paid Fly Machines, use GH Actions instead)
```

#### Oracle Cloud Free Tier (Always Free)

1. Create Compute VM (Ubuntu 22.04, ARM or x86)
2. SSH in:

```bash
ssh ubuntu@your-oracle-instance-ip

# Install Docker
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Clone repo
git clone https://github.com/YOUR-USERNAME/jobbot.git
cd jobbot

# Set secrets
export JOBBOT_MATCHER_BACKEND=heuristic
export JOBBOT_SEND_EMAIL=false

# Run with Docker Compose
docker compose up --build
```

3. Cron job (8-hour schedule):

```bash
crontab -e

# Add:
0 */8 * * * cd /home/ubuntu/jobbot && docker compose up --build
```

---

## Option 4: Docker Compose (Local or VM)

Already configured in `docker-compose.yml`:

```bash
# Build
docker compose build

# Run once
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

---

## Full Environment Variables Reference

```bash
# Profile
JOBBOT_PROFILE_PATH=JobBot/profile.yaml
JOBBOT_RESUME_PATH=JobBot/resume.txt

# Matcher backend
JOBBOT_MATCHER_BACKEND=heuristic        # or "llm"
JOBBOT_LLM_PROVIDER=gemini              # or "groq"
JOBBOT_LLM_MODEL=gemini-2.0-flash
JOBBOT_LLM_API_KEY=your-api-key         # Free from Google AI Studio or Groq

# Email (all required if JOBBOT_SEND_EMAIL=true)
JOBBOT_SEND_EMAIL=false                 # Set to "true" to enable
JOBBOT_SMTP_HOST=smtp.office365.com
JOBBOT_SMTP_PORT=587
JOBBOT_SMTP_USER=your-outlook@outlook.com
JOBBOT_SMTP_PASSWORD=your-app-password
JOBBOT_DIGEST_TO=recipient@outlook.com
JOBBOT_AUTO_CONFIRM_EMAIL=true

# Storage
JOBBOT_SQLITE_PATH=data/jobs.sqlite
JOBBOT_CSV_PATH=data/jobs.csv

# Budget & safety
JOBBOT_MAX_STEPS=12
JOBBOT_MAX_WALL_CLOCK_S=240
JOBBOT_MAX_COST_USD=0.0

# Environment
JOBBOT_ENV=local                        # or "staging" / "production"
```

---

## Health Check Commands

```bash
# Test profile loads
python -c "from agent.profile import load_profile; from pathlib import Path; load_profile(Path('JobBot/profile.yaml')); print('✓ Profile OK')"

# Test config loads
python -c "from agent.config import load_config; load_config(repo_root=Path('.')); print('✓ Config OK')"

# Run tests
python -m pytest -q

# Dry-run without sending email
JOBBOT_MATCHER_BACKEND=heuristic JOBBOT_SEND_EMAIL=false python -m agent.cli --root .

# Dry-run with LLM (requires API key)
JOBBOT_MATCHER_BACKEND=llm JOBBOT_SEND_EMAIL=false python -m agent.cli --root .
```

---

## Troubleshooting Deployments

### GitHub Actions fails: "Module not found"

Ensure `requirements.txt` and `pyproject.toml` are committed:

```bash
git add pyproject.toml requirements.txt
git commit -m "Add dependencies"
git push
```

### Windows Task: "Cannot find path"

Check paths are absolute:

```powershell
$venv = "C:\Users\mps26\Downloads\agent\.venv\Scripts\Activate.ps1"
python -c "import sys; print(sys.executable)"
```

### Docker: "Permission denied"

```bash
sudo usermod -aG docker $USER
newgrp docker
docker compose up
```

### Emails not arriving

1. Verify app password (not login password)
2. Check 2FA is enabled on Outlook account
3. Test SMTP manually:

```bash
python -c "
from tools.smtp_mailer import send
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = 'Test'
msg['From'] = 'your-email@outlook.com'
msg['To'] = 'recipient@outlook.com'
msg.set_content('Test email')

send(msg, host='smtp.office365.com', port=587, user='your-email@outlook.com', password='app-password')
print('✓ Email sent')
"
```

### No jobs found

- Check resume has 50+ characters
- Lower `match_threshold` in `profile.yaml` to 50
- Verify ATS boards are active (Greenhouse, Lever, Workday API up)

---

## Summary

| Option | Cost | Maintenance | Setup Time |
|--------|------|-------------|-----------|
| **GitHub Actions** | $0/month | 0 min/month | 10 min |
| **Windows Task** | $0 | Manual batch | 5 min |
| **Docker + Fly.io** | $0 (free tier only) | Monitoring | 20 min |
| **Oracle Cloud Always Free** | $0 | VM updates | 30 min |

**Recommended:** GitHub Actions + Outlook email. Push once, runs forever.
