# Data handling

Fields that can contain PII: resume text, candidate email (`JOBBOT_DIGEST_TO`), SMTP username.

- Resume stays local / in GitHub secrets files is not used; keep `JobBot/resume.txt` free of government IDs.
- Logs: `redact_secrets` strips `api_key`, `password`, `token`, `authorization`.
- SQLite/CSV retain job metadata (public postings) until you delete `data/`.
- Retention: operator-managed; delete `data/jobs.sqlite` and `data/jobs.csv` to wipe history.
