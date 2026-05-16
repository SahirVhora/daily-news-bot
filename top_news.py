"""
top_news.py - Fetches top global news headlines via BBC, Reuters, AP RSS feeds
and sends a daily digest to Telegram.
Designed to run via GitHub Actions on a schedule.
"""

import feedparser
import requests
import os
import html
from datetime import date


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


def send_telegram(message, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for part in split_message(message):
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()


def split_message(message, max_length=4000):
    if len(message) <= max_length:
        return [message]

    parts = []
    current = []
    current_len = 0

    for line in message.splitlines():
        addition = len(line) + (1 if current else 0)
        if current and current_len + addition > max_length:
            parts.append("\n".join(current))
            current = [line]
            current_len = len(line)
            continue
        current.append(line)
        current_len += addition

    if current:
        parts.append("\n".join(current))
    return parts


def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
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
        print(message)
        print(f"\n[DRY RUN] Message parts: {len(split_message(message))}")
        print(f"\n[DRY RUN] Would send to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent daily top news to Telegram.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch BBC news by category and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
