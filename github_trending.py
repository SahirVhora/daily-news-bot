import os
from datetime import date
from html.parser import HTMLParser

import requests

from digest_common import get_telegram_config, print_dry_run, send_telegram

def fetch_github_trending(limit=10):
    class TrendingParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.repos = []
            self.in_repo_name = False
            self.in_description = False
            self.current = {}
            self.depth = 0

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            # Repo article block
            if tag == "article" and "Box" in attrs.get("class", ""):
                self.current = {}
            # Repo link: /owner/repo
            if tag == "a" and attrs.get("href", "").count("/") == 2 and "h2" not in attrs.get("class", ""):
                href = attrs.get("href", "")
                if href.startswith("/") and href.count("/") == 2:
                    parts = href.strip("/").split("/")
                    if len(parts) == 2 and "." not in parts[0]:
                        self.current["owner"] = parts[0]
                        self.current["repo"] = parts[1]
                        self.current["url"] = f"https://github.com{href}"
            if tag == "p" and "col-9" in attrs.get("class", ""):
                self.in_description = True
                self.current["desc"] = ""

        def handle_data(self, data):
            if self.in_description:
                self.current["desc"] = self.current.get("desc", "") + data

        def handle_endtag(self, tag):
            if tag == "p" and self.in_description:
                self.in_description = False
                if self.current.get("desc"):
                    self.current["desc"] = self.current["desc"].strip()
            if tag == "article":
                if self.current.get("owner") and self.current.get("repo"):
                    self.repos.append(dict(self.current))
                    self.current = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    resp = requests.get("https://github.com/trending", headers=headers, timeout=15)
    resp.raise_for_status()

    parser = TrendingParser()
    parser.feed(resp.text)

    # Fallback: extract via simple pattern if parser misses
    if not parser.repos:
        import re
        matches = re.findall(r'href="/([^/"]+/[^/"]+)"[^>]*>\s*<[^>]+>\s*([^<]+)', resp.text)
        seen = set()
        for owner_repo, _ in matches:
            parts = owner_repo.split("/")
            if len(parts) == 2 and owner_repo not in seen and "." not in parts[0]:
                seen.add(owner_repo)
                parser.repos.append({
                    "owner": parts[0],
                    "repo": parts[1],
                    "url": f"https://github.com/{owner_repo}",
                    "desc": ""
                })
            if len(parser.repos) >= limit:
                break

    return parser.repos[:limit]

def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token, chat_id = get_telegram_config()

    repos = fetch_github_trending()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>🔥 Top 10 Trending GitHub Repos - {today}</b>\n"]

    if not repos:
        lines.append("Could not fetch trending repos today.")
    else:
        for i, r in enumerate(repos, 1):
            name = f"{r['owner']}/{r['repo']}"
            desc = r.get("desc", "")
            url = r.get("url", "")
            lines.append(f"<b>{i}. <a href=\"{url}\">{name}</a></b>")
            if desc:
                lines.append(desc)
            lines.append("")

    message = "\n".join(lines).strip()

    if dry_run:
        print_dry_run(message, f"Would send {len(repos)} trending repos to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch GitHub trending repos and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
