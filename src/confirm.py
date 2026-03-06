#!/usr/bin/env python3
"""
confirm.py — Handles the 30-minute WhatsApp confirmation window.

Run at 7:30 AM (30 mins after job search):
- Reads pending_applications.json
- Checks for SKIP replies in OpenClaw session
- Applies to non-skipped jobs
- Sends WhatsApp summary of what was applied to
"""

import json, sys, time
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent

def load_pending():
    pending_file = WORKSPACE / "pending_applications.json"
    if not pending_file.exists():
        print("No pending applications found")
        return None
    with open(pending_file) as f:
        return json.load(f)

def clear_pending():
    pending_file = WORKSPACE / "pending_applications.json"
    if pending_file.exists():
        pending_file.unlink()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-config", required=True)
    parser.add_argument("--profile-meta", required=True)
    parser.add_argument("--skip", default="", help="SKIP reply from WhatsApp e.g. '1,3' or 'ALL'")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="applied_report.md")
    args = parser.parse_args()

    # Load profile
    with open(args.profile_config) as f:
        profile = json.load(f)
    with open(args.profile_meta) as f:
        meta = json.load(f)

    profile_name = profile.get("name", "User")

    # Load pending
    pending = load_pending()
    if not pending:
        print("Nothing to apply to")
        sys.exit(0)

    jobs = pending.get("jobs", [])
    if not jobs:
        print("No jobs in pending list")
        sys.exit(0)

    print(f"📋 Processing {len(jobs)} pending applications for {profile_name}")

    # Parse skip list
    from apply import parse_skip_reply, run_auto_apply, build_applied_whatsapp_message
    skip_list = parse_skip_reply(args.skip) if args.skip else None
    if skip_list:
        print(f"  SKIP received: {skip_list}")

    # Run applications
    results = run_auto_apply(
        jobs=jobs,
        profile=profile,
        threshold=70,
        dry_run=args.dry_run,
        skip_list=skip_list
    )

    # Build WhatsApp message
    whatsapp_msg = build_applied_whatsapp_message(results, profile_name)
    print("\n" + "="*50)
    print("WhatsApp message to send:")
    print("="*50)
    print(whatsapp_msg)
    print("="*50)

    # Save WhatsApp message for the agent to pick up
    msg_file = WORKSPACE / "whatsapp_applied_message.txt"
    with open(msg_file, "w") as f:
        f.write(whatsapp_msg)
    print(f"\n✅ WhatsApp message saved to {msg_file}")

    # Clear pending
    clear_pending()

    # Write applied report
    applied = [r for r in results if r.get("result", {}).get("status") == "applied"]
    report_lines = [
        f"# Auto-Apply Report — {datetime.now().strftime('%Y-%m-%d')}",
        f"Profile: {profile_name}",
        f"Total applied: {len(applied)}/{len(jobs)}",
        "",
    ]
    for r in results:
        job = r.get("job", {})
        status = r.get("result", {}).get("status", "unknown")
        emoji = "✅" if status == "applied" else "❌" if status == "failed" else "⏭"
        report_lines.append(f"{emoji} **{job.get('title')}** — {job.get('company')}")
        report_lines.append(f"   Score: {job.get('match_score')}% | {job.get('url', '')}")
        if status != "applied":
            report_lines.append(f"   Reason: {r.get('result', {}).get('reason', '')}")
        report_lines.append("")

    with open(args.output, "w") as f:
        f.write("\n".join(report_lines))
    print(f"✅ Applied report saved to {args.output}")

if __name__ == "__main__":
    main()
