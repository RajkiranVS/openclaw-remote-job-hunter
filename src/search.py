#!/usr/bin/env python3
"""
search.py — Multi-platform job fetcher.
Loads platform config from config/platforms.json.
v1.3.0: Added RealWFA, WorkingNomads, RemoteAI, Remote100K
"""
import json, urllib.request, html
from pathlib import Path
try:
    import xml.etree.ElementTree as ET
except:
    pass

CONFIG_DIR = Path(__file__).parent.parent / "config"

def load_platforms():
    with open(CONFIG_DIR / "platforms.json") as f:
        return json.load(f)

def safe_str(val, default=""):
    if val is None:
        return default
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val)


HARD_EXCLUDE_PHRASES = [
    "must be located in", "must reside in", "us only", "usa only",
    "united states only", "requires us work authorization",
    "must be authorized to work in the us", "us citizen",
    "us permanent resident", "requires security clearance",
    "us security clearance", "must be in", "onsite", "on-site", "on site",
    "new york only", "san francisco only", "seattle only",
    "california only", "texas only"
]

# Locations that explicitly indicate Work From Anywhere
WFA_INDICATORS = [
    "worldwide", "anywhere", "global", "work from anywhere", "wfa",
    "international", "no location restriction", "remote worldwide",
    "fully remote", "100% remote"
]

# Country/region-restricted patterns that are NOT WFA (for WFA-strict mode)
REGION_RESTRICTED = [
    "australia", "new zealand", "anz", "united kingdom", "uk only",
    "europe only", "eu only", "germany", "france", "spain", "ireland",
    "canada only", "brazil", "india only", "uae only", "dubai only",
    "philippines", "poland", "czech", "austria", "netherlands"
]

def is_location_ok(location, wfa_strict=False):
    if not location:
        return True
    loc = location.lower().strip()
    if any(phrase in loc for phrase in HARD_EXCLUDE_PHRASES):
        return False
    if wfa_strict:
        if any(ind in loc for ind in WFA_INDICATORS):
            return True
        if any(r in loc for r in REGION_RESTRICTED):
            return False
    return True

def is_wfa(location):
    """Returns True if the job is explicitly WFA/Worldwide."""
    if not location or location.strip() == "":
        return True
    loc = location.lower().strip()
    return any(ind in loc for ind in WFA_INDICATORS)

def fetch_remotive(config, domain):
    category = config["category_map"].get(domain, domain)
    url = f"{config['base_url']}?category={category}&limit=100"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            jobs = data.get("jobs", [])
            print(f"  Remotive [{category}]: {len(jobs)} jobs")
            return [{
                "title": html.unescape(safe_str(job.get("title", ""))),
                "company": html.unescape(safe_str(job.get("company_name", ""))),
                "salary": safe_str(job.get("salary", "")) or "Not listed",
                "url": safe_str(job.get("url", "")),
                "location": safe_str(job.get("candidate_required_location", "Worldwide")),
                "posted": safe_str(job.get("publication_date", ""))[:10],
                "tags": ", ".join(job.get("tags", [])[:5]),
                "description": safe_str(job.get("description", "")),
                "source": "Remotive"
            } for job in jobs]
    except Exception as e:
        print(f"  Remotive error: {e}")
        return []

def fetch_jobicy(config, domain):
    tags = config["tag_map"].get(domain, [])
    results = []
    seen_ids = set()
    for tag in tags:
        url = f"{config['base_url']}?count=20&tag={tag}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                jobs = data.get("jobs", [])
                print(f"  Jobicy [{tag}]: {len(jobs)} jobs")
                for job in jobs:
                    jid = str(job.get("id", ""))
                    if jid in seen_ids:
                        continue
                    seen_ids.add(jid)
                    job_loc = html.unescape(safe_str(job.get("jobGeo", "")))
                    if not is_location_ok(job_loc, wfa_strict=True):
                        continue
                    results.append({
                        "title": html.unescape(safe_str(job.get("jobTitle", ""))),
                        "company": html.unescape(safe_str(job.get("companyName", ""))),
                        "salary": "Not listed",
                        "url": safe_str(job.get("url", "")),
                        "location": safe_str(job.get("jobGeo", "Worldwide")),
                        "posted": safe_str(job.get("pubDate", ""))[:10],
                        "tags": safe_str(job.get("jobIndustry", "")),
                        "description": html.unescape(safe_str(job.get("jobDescription", ""))),
                        "source": "Jobicy"
                    })
        except Exception as e:
            print(f"  Jobicy [{tag}] error: {e}")
    return results

def fetch_remoteok(config, phrases):
    url = config["base_url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            jobs = [j for j in data if isinstance(j, dict) and j.get("position")]
            print(f"  RemoteOK: {len(jobs)} total jobs")
            results = []
            for job in jobs:
                position = html.unescape(safe_str(job.get("position", "")))
                tags = " ".join(job.get("tags", []))
                if not any(p in (position + " " + tags).lower() for p in phrases):
                    continue
                sal_min = job.get("salary_min") or 0
                sal_max = job.get("salary_max") or 0
                try:
                    sal_min = int(sal_min) if sal_min else 0
                    sal_max = int(sal_max) if sal_max else 0
                except:
                    sal_min = sal_max = 0
                salary_str = f"${sal_min//1000}K-${sal_max//1000}K USD" if sal_min and sal_max else \
                             f"${sal_min//1000}K+ USD" if sal_min else "Not listed"
                job_loc = safe_str(job.get("location", ""))
                if not is_location_ok(job_loc):
                    continue
                results.append({
                    "title": position,
                    "company": html.unescape(safe_str(job.get("company", ""))),
                    "salary": salary_str,
                    "url": safe_str(job.get("apply_url") or job.get("url", "")),
                    "location": safe_str(job.get("location", "Worldwide")),
                    "posted": "",
                    "tags": ", ".join(job.get("tags", [])[:5]),
                    "description": safe_str(job.get("description", "")),
                    "source": "RemoteOK"
                })
            print(f"  RemoteOK: {len(results)} relevant matches")
            return results
    except Exception as e:
        print(f"  RemoteOK error: {e}")
        return []

def fetch_wwr(config, domain, phrases):
    import re
    feeds = config["feeds"].get(domain, [])
    results = []
    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read().decode("utf-8")
            root = ET.fromstring(content)
            items = root.findall(".//item")
            matched = 0
            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                region_el = item.find("region")
                pubdate_el = item.find("pubDate")
                desc_el = item.find("description")
                if title_el is None:
                    continue
                raw_title = html.unescape(safe_str(title_el.text, ""))
                if ": " in raw_title:
                    company, job_title = raw_title.split(": ", 1)
                else:
                    company, job_title = "", raw_title
                if not any(p in (job_title + " " + company).lower() for p in phrases):
                    continue
                desc = re.sub(r'<[^>]+>', ' ', safe_str(desc_el.text if desc_el is not None else ""))
                results.append({
                    "title": job_title.strip(),
                    "company": company.strip(),
                    "salary": "Not listed",
                    "url": safe_str(link_el.text if link_el is not None else ""),
                    "location": safe_str(region_el.text if region_el is not None else "Worldwide"),
                    "posted": safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                    "tags": "",
                    "description": desc,
                    "source": "WeWorkRemotely"
                })
                matched += 1
            feed_name = feed_url.split('/')[-1].replace('.rss', '')
            print(f"  WWR [{feed_name}]: {matched} matches from {len(items)} items")
        except Exception as e:
            print(f"  WWR error [{feed_url}]: {e}")
    return results

def fetch_himalayas(config, phrases):
    """Fetch Himalayas jobs across multiple pages (API caps at 20/page)."""
    base_url = config["base_url"]
    pages = config.get("pages", 5)
    page_size = 20
    results = []
    total_fetched = 0
    for page in range(pages):
        offset = page * page_size
        url = f"{base_url}?limit={page_size}&offset={offset}"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                total_fetched += len(jobs)
                for job in jobs:
                    title = html.unescape(safe_str(job.get("title", "")))
                    if not any(p in title.lower() for p in phrases):
                        continue
                    loc_list = job.get("locationRestrictions", [])
                    location = safe_str(loc_list) if loc_list else "Worldwide"
                    if loc_list and not is_wfa(location):
                        continue
                    sal_min = job.get("minSalary") or 0
                    sal_max = job.get("maxSalary") or 0
                    try:
                        sal_min = int(sal_min) if sal_min else 0
                        sal_max = int(sal_max) if sal_max else 0
                    except:
                        sal_min = sal_max = 0
                    salary_str = f"${sal_min//1000}K-${sal_max//1000}K" if sal_min and sal_max else \
                                 f"${sal_min//1000}K+" if sal_min else "Not listed"
                    results.append({
                        "title": title,
                        "company": html.unescape(safe_str(job.get("companyName", ""))),
                        "salary": salary_str,
                        "url": safe_str(job.get("applicationLink") or job.get("guid", "")),
                        "location": location,
                        "posted": safe_str(job.get("pubDate", ""))[:10],
                        "tags": "",
                        "description": html.unescape(safe_str(job.get("description", ""))),
                        "source": "Himalayas"
                    })
        except Exception as e:
            print(f"  Himalayas [page {page}] error: {e}")
            break
    print(f"  Himalayas: {len(results)} matches from {total_fetched} jobs ({pages} pages)")
    return results


# ── v1.3.0: New platform fetchers ─────────────────────────────────────────────

def fetch_realworkfromanywhere(config, domain, phrases):
    """
    realworkfromanywhere.com — hand-curated, every listing verified WFA.
    Uses category-specific RSS feeds (rss.xml).
    """
    import re
    feeds = config.get("feeds", {}).get(domain, [])
    results = []
    seen_urls = set()
    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read().decode("utf-8", errors="replace")
            root = ET.fromstring(content)
            items = root.findall(".//item")
            matched = 0
            for item in items:
                title_el   = item.find("title")
                link_el    = item.find("link")
                desc_el    = item.find("description")
                pubdate_el = item.find("pubDate")
                if title_el is None:
                    continue
                title    = html.unescape(safe_str(title_el.text, ""))
                link     = safe_str(link_el.text if link_el is not None else "")
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                desc_raw = safe_str(desc_el.text if desc_el is not None else "")
                desc     = re.sub(r'<[^>]+>', ' ', desc_raw)
                # Extract company from "Title at Company" pattern in title
                company = "See listing"
                if " at " in title:
                    parts = title.rsplit(" at ", 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()
                results.append({
                    "title":       html.unescape(title),
                    "company":     html.unescape(company),
                    "salary":      "Not listed",
                    "url":         link,
                    "location":    "Worldwide (WFA)",
                    "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                    "tags":        "",
                    "description": desc,
                    "source":      "RealWFA"
                })
                matched += 1
            feed_name = feed_url.split("/")[-2]
            print(f"  RealWFA [{feed_name}]: {matched} jobs from {len(items)} items")
        except Exception as e:
            pass  # XML errors suppressed (malformed feed)
    return results


def fetch_workingnomads(config, domain, phrases):
    """
    workingnomads.com — JSON API at /api/exposed_jobs/.
    Filters client-side by title/description against domain phrases.
    """
    import re
    url = config.get("api_url", "https://www.workingnomads.com/api/exposed_jobs/")
    tags = config.get("category_tags", {}).get(domain, [])
    if not tags:
        tags = phrases
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            jobs = json.loads(r.read())
        results = []
        for job in jobs:
            title   = html.unescape(safe_str(job.get("title", "")))
            company = html.unescape(safe_str(job.get("company_name", "") or job.get("company", "")))
            desc    = re.sub(r'<[^>]+>', ' ', safe_str(job.get("description", "")))
            combined = (title + " " + desc).lower()
            if not any(t in combined for t in tags):
                continue
            # Skip if location-restricted
            loc = safe_str(job.get("location", "Worldwide"))
            if not is_location_ok(loc, wfa_strict=True):
                continue
            results.append({
                "title":       title,
                "company":     company,
                "salary":      "Not listed",
                "url":         safe_str(job.get("url", "")),
                "location":    "Worldwide",
                "posted":      safe_str(job.get("pub_date", "") or job.get("created_at", ""))[:10],
                "tags":        safe_str(job.get("tags", "")),
                "description": desc,
                "source":      "WorkingNomads"
            })
        print(f"  WorkingNomads: {len(results)} matches from {len(jobs)} jobs")
        return results
    except Exception as e:
        print(f"  WorkingNomads error: {e}")
        return []


def fetch_remoteai(config, phrases):
    """
    remoteai.io — dedicated AI/ML job board RSS.
    Every listing is AI/ML — no category filtering needed.
    """
    import re
    url = config.get("base_url", "https://remoteai.io/rss")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
        root = ET.fromstring(content)
        items = root.findall(".//item")
        results = []
        for item in items:
            title_el   = item.find("title")
            link_el    = item.find("link")
            desc_el    = item.find("description")
            pubdate_el = item.find("pubDate")
            if title_el is None:
                continue
            title    = html.unescape(safe_str(title_el.text, ""))
            desc_raw = safe_str(desc_el.text if desc_el is not None else "")
            desc     = re.sub(r'<[^>]+>', ' ', desc_raw)
            if not any(p in (title + " " + desc).lower() for p in phrases):
                continue
            if any(p in desc.lower() for p in HARD_EXCLUDE_PHRASES):
                continue
            company = "See listing"
            for sep in [" — ", " - ", " at ", " @ "]:
                if sep in title:
                    parts   = title.split(sep, 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()
                    break
            results.append({
                "title":       html.unescape(title),
                "company":     html.unescape(company),
                "salary":      "Not listed",
                "url":         safe_str(link_el.text if link_el is not None else ""),
                "location":    "Worldwide",
                "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                "tags":        "ai, ml",
                "description": desc,
                "source":      "RemoteAI"
            })
        print(f"  RemoteAI: {len(results)} matches from {len(items)} items")
        return results
    except Exception as e:
        print(f"  RemoteAI error: {e}")
        return []


def fetch_remote100k(config, phrases):
    """
    remote100k.com — manually vetted $100K+ remote roles only.
    Strong signal — low noise, high quality listings.
    """
    import re
    url = config.get("base_url", "https://remote100k.com/rss")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
        root = ET.fromstring(content)
        items = root.findall(".//item")
        results = []
        for item in items:
            title_el   = item.find("title")
            link_el    = item.find("link")
            desc_el    = item.find("description")
            pubdate_el = item.find("pubDate")
            if title_el is None:
                continue
            title    = html.unescape(safe_str(title_el.text, ""))
            desc_raw = safe_str(desc_el.text if desc_el is not None else "")
            desc     = re.sub(r'<[^>]+>', ' ', desc_raw)
            combined = (title + " " + desc).lower()
            if not any(p in combined for p in phrases):
                continue
            if any(p in combined for p in HARD_EXCLUDE_PHRASES):
                continue
            company = "See listing"
            for sep in [" — ", " - ", " at ", " @ "]:
                if sep in title:
                    parts   = title.split(sep, 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()
                    break
            results.append({
                "title":       html.unescape(title),
                "company":     html.unescape(company),
                "salary":      "$100K+",
                "url":         safe_str(link_el.text if link_el is not None else ""),
                "location":    "Worldwide",
                "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                "tags":        "",
                "description": desc,
                "source":      "Remote100K"
            })
        print(f"  Remote100K: {len(results)} matches from {len(items)} items")
        return results
    except Exception as e:
        print(f"  Remote100K error: {e}")
        return []


def fetch_indeed_eu(phrases, regions=None):
    """
    Indeed Europe RSS feeds for Netherlands and Finland QA jobs.
    indeed.com provides RSS for job searches.
    """
    import re, urllib.parse
    if regions is None:
        regions = [
            ("netherlands", "nl", "Netherlands"),
            ("finland",     "fi", "Finland"),
        ]
    results = []
    # Core QA search terms for Indeed
    search_terms = ["qa automation engineer", "test automation engineer", "sdet", "tosca automation"]
    for term in search_terms[:2]:  # limit to avoid rate limiting
        for country_key, country_code, country_name in regions:
            encoded = urllib.parse.quote(term)
            url = f"https://www.indeed.com/rss?q={encoded}&l={country_name}&radius=100&sort=date"
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=15) as r:
                    content = r.read().decode("utf-8", errors="replace")
                root = ET.fromstring(content)
                items = root.findall(".//item")
                for item in items:
                    title_el   = item.find("title")
                    link_el    = item.find("link")
                    desc_el    = item.find("description")
                    pubdate_el = item.find("pubDate")
                    if title_el is None:
                        continue
                    title    = html.unescape(safe_str(title_el.text, ""))
                    desc_raw = safe_str(desc_el.text if desc_el is not None else "")
                    desc     = re.sub(r'<[^>]+>', ' ', desc_raw)
                    combined = (title + " " + desc).lower()
                    if not any(p in combined for p in phrases):
                        continue
                    # Require visa sponsorship signal
                    visa_signals = ["visa", "sponsor", "relocation", "work permit", "permit"]
                    if not any(v in combined for v in visa_signals):
                        continue
                    results.append({
                        "title":       html.unescape(title),
                        "company":     "See listing",
                        "salary":      "Not listed",
                        "url":         safe_str(link_el.text if link_el is not None else ""),
                        "location":    country_name,
                        "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                        "tags":        "visa sponsorship",
                        "description": desc,
                        "source":      f"Indeed [{country_name}]",
                        "eu_sponsored": True
                    })
            except Exception as e:
                print(f"  Indeed EU [{country_name}] error: {e}")
    print(f"  Indeed EU: {len(results)} visa-sponsored matches")
    return results


def fetch_arbeitnow_eu(phrases, regions=None):
    """Arbeitnow free API - Europe jobs with visa sponsorship"""
    import urllib.request, json, html
    candidates = []
    try:
        all_raw = []
        for page in range(1, 6):
            url = f"https://www.arbeitnow.com/api/job-board-api?visa_sponsorship=true&page={page}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            page_jobs = data.get("data", [])
            if not page_jobs:
                break
            all_raw += page_jobs
        jobs = all_raw
        print(f"  Arbeitnow EU: {len(jobs)} total visa-sponsored jobs (5 pages)")
        phrase_lower = [p.lower() for p in phrases]
        for job in jobs:
            title = html.unescape(str(job.get("title", "")))
            desc  = html.unescape(str(job.get("description", "")))
            tags  = " ".join(job.get("tags", []))
            # Title+tags only — avoids false matches on "automation" in DevOps JDs
            text  = f"{title} {tags}".lower()
            if any(p in text for p in phrase_lower):
                candidates.append({
                    "title":    title,
                    "company":  html.unescape(str(job.get("company_name", ""))),
                    "salary":   "Not listed",
                    "url":      str(job.get("url", "")),
                    "location": str(job.get("location", "Europe (Visa Sponsored)")),
                    "posted":   str(job.get("created_at", ""))[:10],
                    "tags":     tags,
                    "description": desc[:500],
                    "source":   "Arbeitnow [EU Visa]",
                    "eu_sponsored": True
                })
        print(f"  Arbeitnow EU: {len(candidates)} phrase matches")
    except Exception as e:
        print(f"  Arbeitnow EU error: {e}")
    return candidates


def fetch_eu_visa_sponsored(profile_config, phrases):
    """
    EU Visa Sponsored fallback — Netherlands/Finland focus.
    Searches Remotive, Jobicy, WorkingNomads, Indeed EU, Relocate.me, EuropeRemoteJobs.
    Only triggered when WFA matches are below threshold.
    """
    import re
    eu_config = profile_config.get("eu_fallback", {})
    if not eu_config.get("enabled"):
        return []

    allowed_regions = eu_config.get("allowed_regions", [
        "netherlands", "finland", "amsterdam", "helsinki", "nl", "fi"
    ])

    platforms = load_platforms()
    candidates = []

    # ── Remotive ──────────────────────────────────────────────────────────
    try:
        remotive_cfg = platforms.get("remotive", {})
        domain = profile_config.get("domain", "")
        category = remotive_cfg.get("category_map", {}).get(domain, domain)
        url = f"{remotive_cfg['base_url']}?category={category}&limit=100"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            for job in data.get("jobs", []):
                loc = safe_str(job.get("candidate_required_location", "")).lower()
                if not any(r in loc for r in allowed_regions):
                    continue
                desc  = safe_str(job.get("description", "")).lower()
                title = safe_str(job.get("title", "")).lower()
                if not any(p in title + " " + desc for p in phrases):
                    continue
                candidates.append({
                    "title":   html.unescape(safe_str(job.get("title", ""))),
                    "company": html.unescape(safe_str(job.get("company_name", ""))),
                    "salary":  safe_str(job.get("salary", "")) or "Not listed",
                    "url":     safe_str(job.get("url", "")),
                    "location": safe_str(job.get("candidate_required_location", "")),
                    "posted":  safe_str(job.get("publication_date", ""))[:10],
                    "tags":    ", ".join(job.get("tags", [])[:5]),
                    "description": safe_str(job.get("description", "")),
                    "source":  "Remotive [EU]",
                    "eu_sponsored": True
                })
    except Exception as e:
        print(f"  EU Remotive error: {e}")

    # ── Jobicy ────────────────────────────────────────────────────────────
    try:
        jobicy_cfg = platforms.get("jobicy", {})
        tags = jobicy_cfg.get("tag_map", {}).get(profile_config.get("domain", ""), [])
        seen_ids = set()
        for tag in tags[:3]:
            url = f"{jobicy_cfg['base_url']}?count=20&tag={tag}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                for job in data.get("jobs", []):
                    jid = str(job.get("id", ""))
                    if jid in seen_ids:
                        continue
                    seen_ids.add(jid)
                    loc   = html.unescape(safe_str(job.get("jobGeo", ""))).lower()
                    if not any(r in loc for r in allowed_regions):
                        continue
                    title = html.unescape(safe_str(job.get("jobTitle", ""))).lower()
                    desc  = html.unescape(safe_str(job.get("jobDescription", ""))).lower()
                    if not any(p in title + " " + desc for p in phrases):
                        continue
                    candidates.append({
                        "title":   html.unescape(safe_str(job.get("jobTitle", ""))),
                        "company": html.unescape(safe_str(job.get("companyName", ""))),
                        "salary":  "Not listed",
                        "url":     safe_str(job.get("url", "")),
                        "location": safe_str(job.get("jobGeo", "")),
                        "posted":  safe_str(job.get("pubDate", ""))[:10],
                        "tags":    safe_str(job.get("jobIndustry", "")),
                        "description": html.unescape(safe_str(job.get("jobDescription", ""))),
                        "source":  "Jobicy [EU]",
                        "eu_sponsored": True
                    })
    except Exception as e:
        print(f"  EU Jobicy error: {e}")

    # ── Specialist EU boards ──────────────────────────────────────────────
    candidates += fetch_arbeitnow_eu(phrases, allowed_regions)
    candidates += fetch_adzuna(phrases)

    print(f"  EU Visa Sponsored fallback: {len(candidates)} matches "
          f"(Netherlands/Finland)")
    return candidates


def fetch_gulf_anz_jobs(phrases):
    """Jobicy geo-filtered: UAE/Dubai + Australia + New Zealand — visa-sponsored QA roles"""
    import urllib.request, json, html
    candidates = []
    regions = [
        ("united-arab-emirates", "UAE/Dubai"),
        ("australia",            "Australia"),
        ("new-zealand",          "New Zealand"),
    ]
    phrase_lower = [p.lower() for p in phrases]
    for geo, label in regions:
        for tag in ["qa", "testing", "automation"]:
            try:
                url = f"https://jobicy.com/api/v2/remote-jobs?count=50&geo={geo}&tag={tag}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
                jobs = data.get("jobs", [])
                for job in jobs:
                    title = html.unescape(str(job.get("jobTitle", "")))
                    text  = f"{title} {job.get('jobIndustry','')}".lower()
                    if any(p in text for p in phrase_lower):
                        candidates.append({
                            "title":    title,
                            "company":  html.unescape(str(job.get("companyName", ""))),
                            "salary":   f"{job.get('annualSalaryMin','')}–{job.get('annualSalaryMax','')} {job.get('salaryCurrency','')}".strip("– ") or "Not listed",
                            "url":      str(job.get("url", "")),
                            "location": str(job.get("jobGeo", label)),
                            "posted":   str(job.get("pubDate", ""))[:10],
                            "tags":     str(job.get("jobIndustry", "")),
                            "description": html.unescape(str(job.get("jobDescription", "")))[:500],
                            "source":   f"Jobicy [{label}]",
                            "eu_sponsored": True
                        })
            except Exception:
                pass
    # Deduplicate by URL
    seen = set()
    unique = []
    for j in candidates:
        if j["url"] not in seen:
            seen.add(j["url"])
            unique.append(j)
    print(f"  Gulf+ANZ jobs: {len(unique)} matches (UAE/Australia/NZ)")
    return unique


def fetch_adzuna(phrases):
    """Adzuna API — UAE + Australia + New Zealand QA roles with visa sponsorship"""
    import urllib.request, urllib.parse, json, html, os

    app_id  = os.getenv("ADZUNA_APP_ID",  "508a6def")
    app_key = os.getenv("ADZUNA_APP_KEY", "bd813a11cfe2b60720740fe4ab4a6f4e")

    # country code -> label
    markets = [
        ("au", "Australia"),
        ("nz", "New Zealand"),
        ("sg", "Singapore"),
        ("gb", "UK"),
    ]

    # Software QA only — excludes food/manufacturing/civil QA noise
    title_phrases = [
        "qa automation", "test automation",
        "qa engineer", "qa lead", "qa manager", "qa analyst",
        "sdet", "automation engineer", "automation lead",
        "test engineer", "test lead", "test manager",
        "selenium", "playwright", "tosca", "cypress",
        "software tester", "software quality",
        "automation test", "quality assurance engineer",
        "quality assurance lead", "quality assurance manager",
        "quality assurance analyst"
    ]

    candidates = []
    phrase_lower = [p.lower() for p in phrases]

    for country, label in markets:
        for keyword in ["qa automation", "test automation", "quality assurance"]:
            try:
                params = urllib.parse.urlencode({
                    "app_id":         app_id,
                    "app_key":        app_key,
                    "results_per_page": 20,
                    "what":           keyword,
                    "content-type":   "application/json",
                })
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{params}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = json.loads(r.read().decode())
                jobs = data.get("results", [])
                for job in jobs:
                    title = html.unescape(str(job.get("title", "")))
                    # Title-only match to avoid false positives
                    title_lower = title.lower()
                    if any(p in title_lower for p in title_phrases):
                        desc = html.unescape(str(job.get("description", "")))
                        salary_min = job.get("salary_min", "")
                        salary_max = job.get("salary_max", "")
                        salary = f"{salary_min}–{salary_max}".strip("–") if salary_min or salary_max else "Not listed"
                        candidates.append({
                            "title":       title,
                            "company":     html.unescape(str(job.get("company", {}).get("display_name", ""))),
                            "salary":      salary,
                            "url":         str(job.get("redirect_url", "")),
                            "location":    str(job.get("location", {}).get("display_name", label)),
                            "posted":      str(job.get("created", ""))[:10],
                            "tags":        keyword,
                            "description": desc[:500],
                            "source":      f"Adzuna [{label}]",
                            "eu_sponsored": True
                        })
            except Exception as e:
                print(f"  Adzuna [{label}/{keyword}] error: {e}")

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in candidates:
        if j["url"] not in seen and j["title"]:
            seen.add(j["url"])
            unique.append(j)

    print(f"  Adzuna Gulf+ANZ: {len(unique)} matches (UAE/AU/NZ)")
    return unique


def fetch_all(domain, phrases, profile_config):
    platforms = load_platforms()
    all_jobs = []

    # ── Primary: WFA platforms ────────────────────────────────────────────
    if platforms.get("remotive", {}).get("enabled"):
        all_jobs += fetch_remotive(platforms["remotive"], domain)
    if platforms.get("jobicy", {}).get("enabled"):
        all_jobs += fetch_jobicy(platforms["jobicy"], domain)
    if platforms.get("remoteok", {}).get("enabled"):
        all_jobs += fetch_remoteok(platforms["remoteok"], phrases)
    if platforms.get("weworkremotely", {}).get("enabled"):
        all_jobs += fetch_wwr(platforms["weworkremotely"], domain, phrases)
    if platforms.get("himalayas", {}).get("enabled"):
        all_jobs += fetch_himalayas(platforms["himalayas"], phrases)
    if platforms.get("realworkfromanywhere", {}).get("enabled") and profile_config.get("realwfa_enabled", True):
        all_jobs += fetch_realworkfromanywhere(platforms["realworkfromanywhere"], domain, phrases)
    if platforms.get("workingnomads", {}).get("enabled"):
        all_jobs += fetch_workingnomads(platforms["workingnomads"], domain, phrases)
    if platforms.get("remoteai", {}).get("enabled"):
        all_jobs += fetch_remoteai(platforms["remoteai"], phrases)
    if platforms.get("remote100k", {}).get("enabled"):
        all_jobs += fetch_remote100k(platforms["remote100k"], phrases)

    # ── Deduplicate WFA jobs ──────────────────────────────────────────────
    seen = set()
    unique = []
    for j in all_jobs:
        if j["url"] not in seen and j["title"]:
            seen.add(j["url"])
            unique.append(j)

    # ── EU Fallback: trigger if WFA matches below threshold ───────────────
    eu_config = profile_config.get("eu_fallback", {})
    if eu_config.get("enabled"):
        threshold = eu_config.get("min_wfa_threshold", 8)
        if len(unique) < threshold:
            print(f"\n  ⚠️  Only {len(unique)} WFA matches — triggering EU visa-sponsored fallback (threshold: {threshold})")
            eu_jobs = fetch_eu_visa_sponsored(profile_config, phrases)
            for j in eu_jobs:
                if j["url"] not in seen and j["title"]:
                    seen.add(j["url"])
                    unique.append(j)
        else:
            print(f"\n  ✅ {len(unique)} WFA matches — EU fallback not needed")

    print(f"\n  Total unique jobs: {len(unique)}")
    return unique
