# JobBot

Specialized bot on the from-scratch runtime: ingest ATS boards → dedupe → match → CSV → one Outlook digest.

## Local run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
make test
$env:JOBBOT_MATCHER_BACKEND="heuristic"
$env:JOBBOT_SEND_EMAIL="false"
python -m agent.cli --root .
```

Edit `JobBot/profile.yaml` (skills, location, experience, ATS board tokens) and `JobBot/resume.txt`.

Free Outlook digest: set `JOBBOT_SEND_EMAIL=true` plus SMTP user/app-password and `JOBBOT_DIGEST_TO`. Free LLM matching: Gemini or Groq API key and `JOBBOT_MATCHER_BACKEND=llm`.

Hosting: `docs/hosting.md`.
