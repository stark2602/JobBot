# JobBot Run Guide — Fresher Seeking Jobs in North India

This guide walks you through running the JobBot to search for entry-level jobs across Google, Microsoft, Amazon, Flipkart, and Swiggy, targeting Remote, Delhi, Noida, and Gurgaon roles.

## Prerequisites

- **Python 3.12+** installed
- **Git** installed
- A terminal/PowerShell with internet access

---

## Quick Start (5 minutes)

### 1. Clone or navigate to the repo

```powershell
cd c:\Users\mps26\Downloads\agent
```

### 2. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -e ".[dev]"
```

### 4. Run with heuristic matcher (offline, no API key needed)

```powershell
$env:JOBBOT_MATCHER_BACKEND = "heuristic"
$env:JOBBOT_SEND_EMAIL = "false"
python -m agent.cli --root .
```

Expected output:
- Fetches jobs from configured ATS boards (Google, Microsoft, Amazon, Flipkart, Swiggy, Atlassian, Figma, ThoughtWorks)
- Deduplicates jobs using MD5 hash
- Scores matches (heuristic: keyword overlap with resume)
- Exports results to `data/jobs.csv`
- Writes dedup database to `data/jobs.sqlite`

---

## Profile Configuration

The profile is pre-configured for a fresher in North India:

```yaml
# JobBot/profile.yaml
candidate:
  experience_years: 1          # Fresher level
  skills:                      # 9 core languages/frameworks
    - Python                   # Entry-level backend
    - Java                     # Banking/enterprise roles
    - JavaScript               # Frontend basics
    - React                    # Modern frontend
    - HTML/CSS                 # Full-stack foundation
    - SQL                      # Database queries
    - Git                      # Version control
    - AWS                      # Cloud beginnings
    - Django                   # Python web framework
  locations:                   # North India focus
    - Remote
    - Delhi
    - Noida
    - Gurgaon

search:
  max_age_hours: 12             # Last 12 hours only
  match_threshold: 60          # Lower threshold for fresher roles
  email_min_score: 65          # Email only high-confidence matches
  exclude_terms:               # Reject unsuitable roles
    - Staffing Agency
    - C2C
    - Security Clearance
    - Unpaid
    - Consultant

sources:
  greenhouse:                  # Direct ATS for major companies
    - google
    - microsoft
    - amazon
    - flipkart
    - swiggy
  lever:                       # Design/tech company focus
    - atlassian
    - figma
    - thoughtworks
  workday: []                  # Add if targeting enterprise hiring
```

---

## Option A: Run Offline (No API Keys)

**Recommended for testing and daily automation.**

Uses heuristic matching (keyword overlap with resume). No cost.

```powershell
$env:JOBBOT_MATCHER_BACKEND = "heuristic"
$env:JOBBOT_SEND_EMAIL = "false"          # Don't send email for now
python -m agent.cli --root .
```

Check results:
```powershell
cat data/jobs.csv  # CSV export of matches
```

---

## Option B: Run with LLM Scorer (Free API)

**Better matching, but requires a free API key.**

### Step 1: Get a free API key

Choose **one**:

#### Gemini (Google) — Recommended
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Get API Key**
3. Create a new API key (free tier: 60 requests/minute, 1500 requests/day)

#### Groq — Fast & Free
1. Go to [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create an API key

### Step 2: Set environment variables

```powershell
# For Gemini (default)
$env:JOBBOT_LLM_PROVIDER = "gemini"
$env:JOBBOT_LLM_MODEL = "gemini-2.0-flash"
$env:JOBBOT_LLM_API_KEY = "your-gemini-api-key-here"

# OR for Groq
$env:JOBBOT_LLM_PROVIDER = "groq"
$env:JOBBOT_LLM_MODEL = "llama-3.1-8b-instant"
$env:JOBBOT_LLM_API_KEY = "your-groq-api-key-here"
```

### Step 3: Run with LLM

```powershell
$env:JOBBOT_MATCHER_BACKEND = "llm"
$env:JOBBOT_SEND_EMAIL = "false"
python -m agent.cli --root .
```

The LLM will score each job 0-100 and explain why it's a match.

---

## Option C: Send Email Digest (Free Outlook)

**One consolidated HTML email with all matches.**

### Step 1: Generate Outlook App Password

1. Go to [Microsoft Account Security](https://account.microsoft.com/security/)
2. Click **Advanced security options** → **App passwords**
3. Select **Mail** and **Windows Device**, generate a password
4. Copy the 16-character password (spaces removed)

### Step 2: Set email config

```powershell
$env:JOBBOT_SEND_EMAIL = "true"
$env:JOBBOT_SMTP_USER = "your-outlook-email@outlook.com"
$env:JOBBOT_SMTP_PASSWORD = "your-16-char-app-password"
$env:JOBBOT_DIGEST_TO = "recipient@outlook.com"  # Can be same or different
$env:JOBBOT_SMTP_HOST = "smtp.office365.com"
$env:JOBBOT_SMTP_PORT = "587"
```

### Step 3: Run

```powershell
$env:JOBBOT_MATCHER_BACKEND = "heuristic"
python -m agent.cli --root .
```

Email will contain:
- **Top Matches** (90-100%): All details
- **Good Fits** (75-89%): Compact list
- Direct ATS application links

---

## Running Tests

Verify everything is working:

```powershell
python -m pytest -q
```

Expected: 31 tests pass ✓

---

## Scheduling (Run Every 8 Hours)

### Windows Task Scheduler

```powershell
# Create a scheduled task
$trigger = New-JobTrigger -RepetitionInterval (New-TimeSpan -Hours 8) -RepeatIndefinitely -At (Get-Date)
$action = New-ScheduledTaskAction `
  -Execute "PowerShell.exe" `
  -Argument "-NoProfile -WindowStyle Hidden -Command 'cd C:\Users\mps26\Downloads\agent; .\.venv\Scripts\Activate.ps1; $env:JOBBOT_MATCHER_BACKEND=`"heuristic`"; $env:JOBBOT_SEND_EMAIL=`"false`"; python -m agent.cli --root .'"
Register-ScheduledTask -TaskName "JobBot-Fresher-Search" -Trigger $trigger -Action $action -RunLevel Highest
```

Verify:
```powershell
Get-ScheduledTask -TaskName "JobBot-Fresher-Search"
```

---

## File Structure After Run

```
data/
  jobs.sqlite          # Dedup DB with job hashes + scores
  jobs.csv             # CSV export of matched jobs
  
JobBot/
  profile.yaml         # Your profile/search config
  resume.txt           # Your resume
  task.mdc             # Archived task spec
  
src/agent/
  cli.py              # Entry point
  executor.py         # Plan→Act loop
  planner.py          # Decide next skill
  
src/skills/
  ingest_jobs/        # Fetch from ATS
  match_jobs/         # Dedupe + score
  export_csv/         # Write results
  send_digest/        # Email HTML
```

---

## Troubleshooting

### "Profile YAML not found"
```powershell
# Ensure you're in the repo root
cd c:\Users\mps26\Downloads\agent
powershell -Command "ls JobBot/profile.yaml"
```

### "No module named 'agent'"
```powershell
# Reinstall in development mode
pip install -e ".[dev]"
```

### "LLM API request failed"
- Check your API key is set correctly
- Verify internet connection
- Check [Gemini quota](https://aistudio.google.com/app/apikey) or [Groq status](https://status.groq.com)

### "SMTP authentication failed"
- Ensure you generated an **App Password** (not regular password)
- Check email and password are set correctly
- Verify SMTP host is `smtp.office365.com` and port is `587`

### "Jobs not found"
- Check your resume text is substantial (50+ chars)
- Lower `match_threshold` in `profile.yaml` (e.g., 50 instead of 60)
- Search may have 0 results posted in the last 12 hours

---

## Next Steps

1. **Daily run**: Schedule with Task Scheduler (see above)
2. **Customize**: Edit `JobBot/profile.yaml` to adjust skills, locations, or ATS sources
3. **Monitor**: Check `data/jobs.csv` after each run
4. **Apply**: Click links in the HTML email or CSV to apply directly on ATS

---

## Questions?

- See [docs/hosting.md](docs/hosting.md) for free cloud deployment options
- See [docs/data-handling.md](docs/data-handling.md) for PII/data retention policy
- Check [src/skills/](src/skills/) READMEs for skill-specific config

Good luck with your job search! 🚀
