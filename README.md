# remote-job-hunter

> Daily remote job search, NLP resume scoring, skill gap analysis, and WhatsApp delivery — fully automated.

[![version](https://img.shields.io/badge/version-1.3.1-green)](https://github.com/RajkiranVS/openclaw-remote-job-hunter)
[![platforms](https://img.shields.io/badge/job_platforms-10+-orange)](https://github.com/RajkiranVS/openclaw-remote-job-hunter)
[![domains](https://img.shields.io/badge/role_domains-4-blue)](https://github.com/RajkiranVS/openclaw-remote-job-hunter)
[![license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## What it does

Every day, automatically:

1. 🔍 **Scrapes 10+ job platforms** — Remotive, RemoteOK, Jobicy, WeWorkRemotely, Himalayas, WorkingNomads, Adzuna (AU/NZ/SG/UK), Arbeitnow EU, and more
2. 📊 **Scores every job 0–100%** against your resume using NLP keyword matching
3. 🎯 **Identifies skill gaps** ranked by market frequency — tells you exactly what to learn
4. 📱 **Delivers a WhatsApp summary** of top matches via OpenClaw agent
5. 🌍 **EU visa-sponsored fallback** — automatically widens search when local supply is thin

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    remote-job-hunter                     │
│                                                         │
│  search.py          scorer.py           report.py       │
│  ──────────         ──────────          ──────────      │
│  10+ platforms  →   NLP scoring    →    MD report       │
│  EU fallback        Resume parse        Gap analysis    │
│  Adzuna API         Keyword match       WhatsApp msg    │
│  Dedup/filter       Title exclude                       │
└──────────────────────────┬──────────────────────────────┘
                           │
                    OpenClaw Agent
                    (Haiku-class LLM)
                           │
                    WhatsApp delivery
                    via cron schedule
```

---

## Why it beats manual job searching

| Manual search | remote-job-hunter |
|---|---|
| 1–2 hours/day | 0 minutes/day |
| Miss jobs posted overnight | Catches everything daily at 10 AM |
| No idea how well you match | Exact % score per job |
| No skill gap visibility | Top gaps ranked by market frequency |
| Apply to everything | Only surface strong matches (70%+) |
| Single platform | 10+ platforms including geo-targeted boards |

---

## Quick Start

### 1. Install dependencies

```bash
pip install requests python-docx pymupdf --break-system-packages
```

### 2. Set up API credentials

```bash
cp .env.example .env
# Edit .env and add your Adzuna credentials (free at developer.adzuna.com)
# ADZUNA_APP_ID=your_app_id
# ADZUNA_APP_KEY=your_app_key
```

### 3. Configure your profile

```bash
cp config/profile.template.json my-profile.json
# Edit my-profile.json with your name, resume path, target salary, domain
```

### 4. Run your first search

```bash
python3 src/main.py \
  --profile-config my-profile.json \
  --profile-meta profiles/ai-ml.json \
  --output daily_report.md
```

### 5. Read your results

```bash
cat daily_report.md
```

---

## Supported Role Domains

| Domain | Target Roles |
|---|---|
| `ai-ml` | AI/ML Architect, MLOps Engineer, GenAI Engineer, Data Scientist, LLM Engineer |
| `qa-automation` | TOSCA Lead, Test Architect, QA Automation Engineer, SDET, Test Lead |
| `software-dev` | Full Stack, Backend, Frontend, Software Engineer |
| `devops` | DevOps Engineer, Platform Engineer, SRE, Cloud Engineer |

---

## Sample Output

```
📊 Summary:
   Total jobs: 139
   🟢 80%+ match: 8

⚠️  Top skill gaps:
   - Playwright (13 jobs) — Medium term
   - TypeScript (8 jobs) — Medium term
   - Java (3 jobs) — Medium term

📋 Top matches:
   1. Senior QA Automation Engineer — Tech Aalto (100%) — AU
   2. Automation Tester — Hudson (100%) — AU
   3. Test Automation Engineer — Accenture (100%) — AU
```

---

## Daily WhatsApp automation (OpenClaw)

Add this to your OpenClaw cron to get daily WhatsApp job summaries:

```bash
openclaw cron add --agent your-agent --name "Daily Job Search" \
  --cron "0 10 * * *" --tz "Asia/Kolkata" \
  --model "anthropic/claude-haiku-4-5-20251001" \
  --announce --channel whatsapp --to "+91XXXXXXXXXX" \
  --message "Run: cd /path/to/remote-job-hunter && python3 src/main.py \
    --profile-config my-profile.json \
    --profile-meta profiles/ai-ml.json \
    --output ~/daily_report.md. \
    Then read ~/daily_report.md and report the results."
```

---

## How the scorer works

1. **Resume parsing** — extracts text from `.docx` or `.pdf`, handles XML-split phrases
2. **Keyword expansion** — pipe-separated skill lists (`"API | UI | Mobile Testing"`) are expanded into full phrases
3. **Domain keyword matching** — 80+ keywords per domain, curated per role family
4. **Title exclusion filter** — hard-caps off-domain roles (e.g. DevOps jobs scoring high on cloud keywords for an AI/ML profile)
5. **Minimum signal threshold** — jobs with fewer than 3 extractable skills are marked N/A rather than inflated

---

## EU Visa Sponsorship Fallback

When fewer than N work-from-anywhere matches are found (configurable), the pipeline automatically:
- Queries Arbeitnow for EU visa-sponsored roles
- Queries Adzuna across AU, NZ, SG, UK markets
- Merges and deduplicates with the main results

Configure in your profile:

```json
"eu_fallback": {
  "enabled": true,
  "min_wfa_threshold": 15,
  "allowed_regions": ["netherlands", "germany", "ireland", "finland", ...],
  "require_visa_sponsorship": true
}
```

---

## Project Structure

```
remote-job-hunter/
├── src/
│   ├── main.py          # Entry point, orchestration
│   ├── search.py        # 10+ platform scrapers + EU fallback
│   ├── scorer.py        # NLP resume scoring engine
│   ├── report.py        # Markdown report + WhatsApp message generation
│   ├── apply.py         # Auto-apply engine (Playwright)
│   ├── confirm.py       # Application confirmation workflow
│   ├── gaps.py          # Skill gap analysis
│   └── tailor.py        # Per-job resume tailoring
├── config/
│   ├── skill_keywords.json     # Domain keyword lists
│   └── profile.template.json  # Profile template
├── profiles/
│   ├── ai-ml.json              # AI/ML domain meta
│   └── qa-automation.json      # QA domain meta
├── .env.example
└── README.md
```

---

## Roadmap

- ✅ v1.0.0 — Multi-platform search, NLP scoring, skill gap analysis
- ✅ v1.1.0 — WhatsApp delivery via OpenClaw cron
- ✅ v1.2.0 — EU visa-sponsored fallback (Arbeitnow)
- ✅ v1.3.0 — Adzuna AU/NZ/SG/UK integration, title exclude filter, scorer fixes
- ✅ v1.3.1 — Resume pipe-expansion, QA keyword expansion, cron delivery fix
- 🔄 v1.4.0 — Playwright auto-apply engine (libnss3 dependency fix + WSL support)
- 📋 v1.5.0 — Cover letter generation per application
- 📋 v1.6.0 — Application tracking dashboard
- 📋 v2.0.0 — MCP server wrapper (integrate with MCPilot)

---

## Requirements

```
requests
python-docx
pymupdf>=1.23.0
python-dotenv
```

Optional (for auto-apply):
```
playwright
```

---

## Security

- ✅ No credentials stored in profile/config files — all via `.env`
- ✅ Outbound requests only to public job board APIs
- ✅ All data written locally — nothing sent externally
- ✅ Profile JSONs excluded from git via `.gitignore`

---

## Author

**Rajkiran Veldur** — Senior AI/ML Solutions Architect  
[linkedin.com/in/rajkiranveldur](https://linkedin.com/in/rajkiranveldur) · [github.com/RajkiranVS/openclaw-remote-job-hunter](https://github.com/RajkiranVS/openclaw-remote-job-hunter)

---

*Built to solve my own job search problem. Now open source.*