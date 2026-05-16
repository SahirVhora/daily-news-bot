import feedparser
import os
import sys
from datetime import date

from digest_common import get_telegram_config, print_dry_run, send_telegram

def fetch_news(feed_url, limit=10):
    feed = feedparser.parse(feed_url)
    stories = []
    for entry in feed.entries[:limit]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        stories.append((title, summary, link))
    return stories

def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token, chat_id = get_telegram_config()

    uk_stories = fetch_news("http://feeds.bbci.co.uk/news/rss.xml")
    india_stories = fetch_news("https://feeds.feedburner.com/ndtvnews-top-stories")

    today = date.today().strftime("%A, %d %B %Y")

    # UK message
    uk_lines = [f"<b>🇬🇧 Top 10 UK News - {today}</b>\n"]
    for i, (title, summary, link) in enumerate(uk_stories, 1):
        uk_lines.append(f"<b>{i}. {title}</b>")
        if summary:
            uk_lines.append(summary)
        if link:
            uk_lines.append(f'<a href="{link}">Read more</a>')
        uk_lines.append("")
    uk_msg = "\n".join(uk_lines).strip()

    # India message
    india_lines = [f"<b>🇮🇳 Top 10 India News - {today}</b>\n"]
    for i, (title, summary, link) in enumerate(india_stories, 1):
        india_lines.append(f"<b>{i}. {title}</b>")
        if summary:
            india_lines.append(summary)
        if link:
            india_lines.append(f'<a href="{link}">Read more</a>')
        india_lines.append("")
    india_msg = "\n".join(india_lines).strip()

    if dry_run:
        print_dry_run(
            uk_msg,
            f"Would send {len(uk_stories)} UK stories to Telegram",
        )
        print("\n---\n")
        print_dry_run(
            india_msg,
            f"Would send {len(india_stories)} India stories to Telegram",
        )
        return

    send_telegram(uk_msg, token, chat_id)
    send_telegram(india_msg, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch UK + India news RSS and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
