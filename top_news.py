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
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
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

    # Telegram has a 4096 char limit per message - truncate safely
    if len(message) > 4000:
        message = message[:3990] + "\n..."

    send_telegram(message, token, chat_id)
    print("Sent daily top news to Telegram.")


if __name__ == "__main__":
    main()
