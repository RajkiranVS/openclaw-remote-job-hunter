# remote-job-hunter

> AI-powered remote job search automation skill for [OpenClaw](https://openclaw.ai).

[![clawhub](https://img.shields.io/badge/clawhub-remote--job--hunter-blue)](https://clawhub.dev/skills/remote-job-hunter)

## What it does

- 🔍 Searches **5 job platforms** daily (Remotive, RemoteOK, Jobicy, WeWorkRemotely, Himalayas)
- 📊 **Scores each job** against your resume using NLP keyword matching
- 🎯 **Skill gap analysis** — tells you exactly what to upskill, categorised by effort
- 📱 Generates a **WhatsApp-ready daily report** via OpenClaw agent
- ⚙️ **Fully config-driven** — one JSON profile per person, zero hardcoding
- 🤖 **Auto-apply engine** (Playwright) — coming in v1.1.0

## Install
```bash
npx clawhub install remote-job-hunter
```

## Quick Start
```bash
# Copy and fill in your profile
cp config/profile.template.json my-profile.json

# Run
python3 src/main.py \
  --profile-config my-profile.json \
  --profile-meta profiles/ai-ml.json \
  --output daily_report.md
```

## Supported Domains

| Domain | Example Roles |
|--------|--------------|
| `ai-ml` | AI/ML Architect, MLOps Engineer, GenAI Engineer |
| `qa-automation` | TOSCA Lead, Test Architect, QA Automation Engineer |
| `software-dev` | Full Stack Engineer, Backend Developer |
| `devops` | DevOps Engineer, Platform Engineer, SRE |

## Author

**Rajkiran Veldur** — AI/ML Solutions Architect  
[linkedin.com/in/rajkiranveldur](https://linkedin.com/in/rajkiranveldur)
