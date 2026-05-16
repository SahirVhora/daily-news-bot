"""
top_news.py - Fetches top global news headlines via BBC, Reuters, AP RSS feeds
and sends a daily digest to Telegram.
Designed to run via GitHub Actions on a schedule.
"""

import feedparser
import os
import html
from datetime import date

from digest_common import get_telegram_config, print_dry_run, send_telegram


FEEDS = [
    ("World", "http://feeds.bbci.co.uk/news/world/rss.xml", "🌍"),
    ("UK", "http://feeds.bbci.co.uk/news/uk/rss.xml", "🇬🇧"),
    ("Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml", "💻"),
    ("Business", "http://feeds.bbci.co.uk/news/business/rss.xml", "📈"),
    ("Science", "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "🔬"),
]


def fetch_feed(url, limit=5):
    try:
        feed = feedparser.parse(url)
        stories = []
        for entry in feed.entries[:limit]:
            title = html.escape(entry.get("title", "").strip())
            link = entry.get("link", "").strip()
            stories.append((title, link))
        return stories
    except Exception as e:
        return []

def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token, chat_id = get_telegram_config()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>📰 Daily Top News - {today}</b>\n"]

    for section, url, emoji in FEEDS:
        stories = fetch_feed(url, limit=5)
        if not stories:
            continue
        lines.append(f"\n<b>{emoji} {section}</b>")
        for i, (title, link) in enumerate(stories, 1):
            if link:
                lines.append(f'{i}. <a href="{link}">{title}</a>')
            else:
                lines.append(f"{i}. {title}")

    lines.append("\n<i>Source: BBC News RSS • Updated daily at 7:00 AM UTC</i>")

    message = "\n".join(lines)

    if dry_run:
        print_dry_run(message, "Would send to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent daily top news to Telegram.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch BBC news by category and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
