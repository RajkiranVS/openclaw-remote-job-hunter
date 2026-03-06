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

def fetch_realworkfromanywhere(config, phrases):
    """
    realworkfromanywhere.com — hand-curated, every listing verified WFA.
    No location filtering needed — board guarantees global hiring.
    """
    import re
    url = config.get("base_url", "https://www.realworkfromanywhere.com/rss")
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
            company_match = re.search(r'(?:at|@)\s+([A-Z][^\n<,]{2,40})', desc_raw)
            company = company_match.group(1).strip() if company_match else "See listing"
            results.append({
                "title":       title,
                "company":     company,
                "salary":      "Not listed",
                "url":         safe_str(link_el.text if link_el is not None else ""),
                "location":    "Worldwide",
                "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                "tags":        "",
                "description": desc,
                "source":      "RealWFA"
            })
        print(f"  RealWFA: {len(results)} matches from {len(items)} items")
        return results
    except Exception as e:
        print(f"  RealWFA error: {e}")
        return []


def fetch_workingnomads(config, domain, phrases):
    """
    workingnomads.com — curated global remote jobs, RSS per category.
    Feeds defined per domain in platforms.json.
    """
    import re
    feeds = config.get("feeds", {}).get(domain, [])
    results = []
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
                desc_raw = safe_str(desc_el.text if desc_el is not None else "")
                desc     = re.sub(r'<[^>]+>', ' ', desc_raw)
                if not any(p in (title + " " + desc).lower() for p in phrases):
                    continue
                company = "See listing"
                if " at " in title:
                    parts = title.rsplit(" at ", 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()
                results.append({
                    "title":       html.unescape(title),
                    "company":     html.unescape(company),
                    "salary":      "Not listed",
                    "url":         safe_str(link_el.text if link_el is not None else ""),
                    "location":    "Worldwide",
                    "posted":      safe_str(pubdate_el.text if pubdate_el is not None else "")[:16],
                    "tags":        "",
                    "description": desc,
                    "source":      "WorkingNomads"
                })
                matched += 1
            feed_name = feed_url.split("category=")[-1].split("&")[0]
            print(f"  WorkingNomads [{feed_name}]: {matched} matches from {len(items)} items")
        except Exception as e:
            print(f"  WorkingNomads error [{feed_url}]: {e}")
    return results


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


def fetch_all(domain, phrases, profile_config):
    platforms = load_platforms()
    all_jobs = []
    # ── Existing platforms ────────────────────────────────────────────────
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
    # ── v1.3.0 New platforms ──────────────────────────────────────────────
    if platforms.get("realworkfromanywhere", {}).get("enabled"):
        all_jobs += fetch_realworkfromanywhere(platforms["realworkfromanywhere"], phrases)
    if platforms.get("workingnomads", {}).get("enabled"):
        all_jobs += fetch_workingnomads(platforms["workingnomads"], domain, phrases)
    if platforms.get("remoteai", {}).get("enabled"):
        all_jobs += fetch_remoteai(platforms["remoteai"], phrases)
    if platforms.get("remote100k", {}).get("enabled"):
        all_jobs += fetch_remote100k(platforms["remote100k"], phrases)
    # ── Deduplicate by URL ────────────────────────────────────────────────
    seen = set()
    unique = []
    for j in all_jobs:
        if j["url"] not in seen and j["title"]:
            seen.add(j["url"])
            unique.append(j)
    print(f"\n  Total unique jobs: {len(unique)}")
    return unique
