#!/usr/bin/env python3
"""Weekly GitHub repo health digest for GitHub Actions."""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from digest_common import get_telegram_config, print_dry_run, send_telegram

OWNER = "SahirVhora"
NOW = datetime.now(timezone.utc)


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


def get_repos():
    return gh_json(
        "repo",
        "list",
        OWNER,
        "--limit",
        "100",
        "--json",
        "name,pushedAt,updatedAt,isFork,isArchived,visibility,description",
        timeout=60,
    )


def get_issue_pr_counts(repo: str) -> tuple[str, int, int]:
    issues = gh_json(
        "issue",
        "list",
        "--repo",
        f"{OWNER}/{repo}",
        "--state",
        "open",
        "--json",
        "number",
        "--limit",
        "100",
        timeout=20,
    )
    prs = gh_json(
        "pr",
        "list",
        "--repo",
        f"{OWNER}/{repo}",
        "--state",
        "open",
        "--json",
        "number",
        "--limit",
        "100",
        timeout=20,
    )
    return repo, len(issues or []), len(prs or [])


def days_since(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (NOW - d).days
    except (ValueError, AttributeError):
        return None


def build_message() -> str:
    repos = get_repos()
    if not repos:
        return "⚠️ <b>Weekly Repo Health Digest</b>\n\nCould not list repositories. Check the GH_PAT secret."

    active_repos = [r for r in repos if not r.get("isArchived")]
    repo_names = [r["name"] for r in active_repos]

    counts: dict[str, tuple[int, int]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(get_issue_pr_counts, r): r for r in repo_names}
        for future in as_completed(futures):
            try:
                repo, issues, prs = future.result()
                if issues or prs:
                    counts[repo] = (issues, prs)
            except Exception:
                continue

    total_issues = sum(v[0] for v in counts.values())
    total_prs = sum(v[1] for v in counts.values())

    stale: list[tuple[str, int]] = []
    for repo in active_repos:
        days = days_since(repo.get("pushedAt"))
        if days is not None and days > 30 and not repo.get("isFork", False):
            stale.append((repo["name"], days))

    lines = [
        "🩺 <b>Weekly Repo Health Digest</b>",
        NOW.strftime("%A %d %B %Y"),
        "",
        f"Repos scanned: {len(active_repos)} active / {len(repos)} total",
        f"Open issues: {total_issues} across {len(counts)} repos",
        f"Open PRs: {total_prs}",
        "",
    ]

    if counts:
        lines.append("<b>Needs attention</b>")
        for repo, (issues, prs) in sorted(counts.items(), key=lambda x: -(x[1][0] + x[1][1]))[:15]:
            bits = []
            if issues:
                bits.append(f"{issues} issue(s)")
            if prs:
                bits.append(f"{prs} PR(s)")
            lines.append(f"• {repo}: {', '.join(bits)}")
        lines.append("")

    if stale:
        lines.append("<b>Stale repos, no push in 30d+</b>")
        for name, days in sorted(stale, key=lambda x: -x[1])[:12]:
            lines.append(f"• {name}: {days}d")
        lines.append("")

    if not counts and not stale:
        lines.append("All clear - no open queues or stale active repos found.")

    lines.append("Verdict: use this to pick the next cleanup target, not as a failure list.")
    return "\n".join(lines)


def main(dry_run: bool = False) -> None:
    message = build_message()
    if dry_run:
        print_dry_run(message)
        return
    token, chat_id = get_telegram_config()
    send_telegram(message, token, chat_id)
    print("github_health_digest sent")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send weekly GitHub repo health digest")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
