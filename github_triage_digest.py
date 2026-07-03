#!/usr/bin/env python3
"""Daily GitHub issue triage digest for GitHub Actions."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone

from digest_common import get_telegram_config, print_dry_run, send_telegram

OWNER = "SahirVhora"
NOW = datetime.now(timezone.utc)
URGENT_WORDS = ("crash", "security", "data loss", "broken", "urgent", "blocker", "fail", "error")


def gh_json(*args: str, timeout: int = 30):
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return None
        if not result.stdout.strip():
            return []
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def age_days(date_str: str | None) -> int:
    if not date_str:
        return 0
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (NOW - d).days
    except ValueError:
        return 0


def get_repos() -> list[str]:
    repos = gh_json(
        "repo",
        "list",
        OWNER,
        "--limit",
        "100",
        "--json",
        "name,isArchived",
        timeout=60,
    )
    if not repos:
        return []
    return [r["name"] for r in repos if not r.get("isArchived")]


def classify_issue(issue: dict) -> tuple[str, str]:
    text = f"{issue.get('title', '')} {issue.get('body', '')}".lower()
    labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
    updated_days = age_days(issue.get("updatedAt"))
    created_days = age_days(issue.get("createdAt"))

    if any(word in text for word in URGENT_WORDS) or any("security" in l for l in labels):
        return "P0", "urgent keyword/security signal"
    if updated_days > 30:
        return "STALE", f"no activity for {updated_days}d"
    if created_days <= 1:
        return "NEW", "opened since yesterday"
    if any("bug" in l for l in labels) or any(w in text for w in ("bug", "not working", "exception", "traceback")):
        return "P1", "bug signal"
    if any("feature" in l or "enhancement" in l for l in labels):
        return "P2", "feature/enhancement"
    return "P3", "low/default priority"


def fetch_issues(repo: str) -> tuple[str, list[dict]]:
    issues = gh_json(
        "issue",
        "list",
        "--repo",
        f"{OWNER}/{repo}",
        "--state",
        "open",
        "--json",
        "number,title,createdAt,updatedAt,labels,body,url",
        "--limit",
        "100",
        timeout=30,
    )
    return repo, issues or []


def build_report() -> str:
    repos = get_repos()
    if not repos:
        return "⚠️ <b>Overnight GitHub Triage</b>\n\nCould not list repositories. Check the GH_PAT secret."

    buckets: dict[str, list[str]] = {"P0": [], "P1": [], "P2": [], "P3": [], "STALE": [], "NEW": []}
    total = 0
    repos_with_issues = 0

    for repo in repos:
        repo_name, issues = fetch_issues(repo)
        if issues:
            repos_with_issues += 1
        for issue in issues:
            total += 1
            priority, reason = classify_issue(issue)
            title = issue.get("title", "").strip()
            url = issue.get("url") or f"https://github.com/{OWNER}/{repo_name}/issues/{issue.get('number')}"
            item = f"• {repo_name}#{issue.get('number')}: {title} - {reason}\n  {url}"
            buckets[priority].append(item)

    lines = [
        "🌙 <b>Overnight GitHub Triage</b>",
        NOW.strftime("%A %d %B %Y"),
        "",
    ]

    if total == 0:
        lines.append(f"All clear - zero open issues across {len(repos)} active repos.")
        return "\n".join(lines)

    if buckets["P0"]:
        lines.append(f"URGENT: {len(buckets['P0'])} issue(s) need immediate review.")
        lines.append("")

    sections = [
        ("P0 urgent", "P0", 5),
        ("P1 high - this week", "P1", 8),
        ("New since yesterday", "NEW", 8),
        ("Stale >30d", "STALE", 8),
        ("P2 medium", "P2", 5),
        ("P3 low", "P3", 3),
    ]
    for title, key, max_items in sections:
        items = buckets[key]
        if not items:
            continue
        lines.append(f"<b>{title}</b>")
        lines.extend(items[:max_items])
        if len(items) > max_items:
            lines.append(f"• ... plus {len(items) - max_items} more")
        lines.append("")

    lines.append(f"Summary: {total} open issues across {repos_with_issues} repos. {len(buckets['P0'])} urgent candidates.")
    lines.append("Reflection: this is deterministic triage; use it to spot queues, then inspect before closing or merging.")
    return "\n".join(lines)


def main(dry_run: bool = False) -> None:
    message = build_report()
    if dry_run:
        print_dry_run(message)
        return
    token, chat_id = get_telegram_config()
    send_telegram(message, token, chat_id)
    print("github_triage_digest sent")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send daily GitHub issue triage digest")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
