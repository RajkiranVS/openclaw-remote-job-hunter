---
name: remote-job-hunter
description: AI-powered remote job search, NLP match scoring, and skill gap analysis for OpenClaw agents. Searches 5 platforms (Remotive, RemoteOK, Jobicy, WeWorkRemotely, Himalayas), scores jobs against your resume using NLP keyword matching, and identifies skill gaps with upskill recommendations categorised by effort level. Supports .docx and .pdf resumes. Fully config-driven via JSON profiles. Use when the user says things like "find me remote jobs", "search for jobs matching my resume", "what skills am I missing for these roles", "run my daily job search", or "show me my skill gaps".
---

# Remote Job Hunter

AI-powered remote job search automation skill for OpenClaw. Aggregates jobs from 5 platforms, scores them against your resume, and tells you exactly what to upskill.

## Features

- 🔍 **5-platform aggregation** — Remotive, RemoteOK, Jobicy, WeWorkRemotely, Himalayas
- 📊 **NLP match scoring** — scores each job 0–100% against your resume
- 🎯 **Skill gap analysis** — Quick Win / Medium / Long-term upskill recommendations
- 📄 **Resume support** — .docx (Word) and .pdf formats
- ⚙️ **Fully config-driven** — JSON profiles, zero hardcoding
- 🤖 **Auto-apply engine** (Playwright) — coming in v1.1.0

## Quick Start

### 1. Configure your profile
```bash
cp config/profile.template.json my-profile.json
# Fill in: name, resume_path, email, salary_min_usd, domain
```

### 2. Run job search
```bash
python3 src/main.py \
  --profile-config my-profile.json \
  --profile-meta profiles/ai-ml.json \
  --output daily_report.md
```

### 3. Read your report
```bash
cat daily_report.md
```

## Supported Domains

| Domain | Roles |
|--------|-------|
| `ai-ml` | AI/ML Architect, MLOps Engineer, GenAI Engineer, Data Scientist |
| `qa-automation` | TOSCA Lead, Test Architect, QA Automation Engineer, SDET |
| `software-dev` | Full Stack, Backend, Frontend Engineer |
| `devops` | DevOps Engineer, Platform Engineer, SRE |

## Profile Configuration
```json
{
  "name": "Your Name",
  "domain": "ai-ml",
  "resume_path": "/absolute/path/to/resume.docx",
  "email": "your.jobs@email.com",
  "salary_min_usd": 130000,
  "remote_only": true,
  "dry_run": true,
  "auto_apply_threshold": 80
}
```

## Using with OpenClaw Agent

Add to your cron for daily automated search:
```
Run: cd /path/to/remote-job-hunter && python3 src/main.py
  --profile-config my-profile.json
  --profile-meta profiles/ai-ml.json
  --output daily_report.md
Then read the report and send a WhatsApp summary of top matches and skill gaps.
```

## Output

Generates a `daily_report.md` with:
- Skill gap analysis (in-demand skills vs your resume)
- Jobs sorted by match score (🟢 80%+ · 🟡 50–79% · 🔴 below 50% · ⚪ N/A)
- Direct apply links for each job

## Requirements
```
pymupdf>=1.23.0
```

## Author

**Rajkiran Veldur** — AI/ML Solutions Architect  
[github.com/RajkiranVS/openclaw-remote-job-hunter](https://github.com/RajkiranVS/openclaw-remote-job-hunter)

## Security Notes

- **No credentials stored** — profile.template.json contains no passwords; credentials are managed by OpenClaw auth system
- **Network requests** — src/search.py makes outbound requests only to public job board APIs (Remotive, RemoteOK, Jobicy, WeWorkRemotely, Himalayas)
- **Report sanitization** — daily_report.md contains only job titles, companies, URLs, and scores extracted from public listings
- **No data exfiltration** — all data is written locally; WhatsApp delivery is handled by the OpenClaw agent, not this skill
