import feedparser
import os
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
    token, chat_id = get_telegram_config()
    today = date.today().strftime("%A, %d %B %Y")

    stories = fetch_news("http://feeds.bbci.co.uk/news/rss.xml")
    lines = [f"<b>🇬🇧 Top 10 UK News - {today}</b>\n"]
    for i, (title, summary, link) in enumerate(stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f'<a href="{link}">Read more</a>')
        lines.append("")
    message = "\n".join(lines).strip()

    if dry_run:
        print_dry_run(message, f"Would send {len(stories)} UK stories to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch UK news from BBC RSS and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
