---
name: remote-job-hunter
description: >
  AI-powered remote job search, match scoring, skill gap analysis, and auto-apply
  for OpenClaw agents. Searches 5 platforms (Remotive, RemoteOK, Jobicy,
  WeWorkRemotely, Himalayas), scores jobs against your resume using NLP,
  identifies skill gaps with upskill recommendations, and generates a daily
  WhatsApp-ready report. Use when the user says things like "find me remote jobs",
  "search for jobs matching my resume", "what skills am I missing", or
  "apply to best matching remote jobs".
---

# remote-job-hunter

AI-powered remote job search automation for OpenClaw.

## Quick Start

1. Copy and fill in your profile:
```bash
cp config/profile.template.json my-profile.json
# Edit my-profile.json with your details
```

2. Run job search:
```bash
python3 src/main.py \
  --profile-config my-profile.json \
  --profile-meta profiles/ai-ml.json \
  --output daily_report.md
```

## Supported Domains
- `ai-ml` — AI/ML Architect, MLOps, GenAI Engineer
- `qa-automation` — TOSCA, Selenium, QA Lead, Test Architect
- `software-dev` — Full Stack, Backend, Frontend
- `devops` — DevOps, Platform Engineering, SRE

## Features
- 5-platform job aggregation (no API keys required)
- Resume-aware NLP match scoring (0–100%)
- Skill gap analysis with Quick Win / Medium / Long-term categorisation
- Daily report in markdown — ready for WhatsApp delivery via OpenClaw agent
- Fully config-driven — zero hardcoding
- Auto-apply engine (Playwright) — coming in v1.1.0
