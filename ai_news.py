import feedparser
import os
from datetime import date, datetime, timezone, timedelta

from digest_common import get_telegram_config, print_dry_run, send_telegram

FEEDS = [
    ("The Verge AI",        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT Tech Review AI",  "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",      "https://venturebeat.com/category/ai/feed/"),
    ("Google DeepMind",     "https://deepmind.google/blog/rss.xml"),
    ("OpenAI Blog",         "https://openai.com/blog/rss.xml"),
    ("Hugging Face Blog",   "https://huggingface.co/blog/feed.xml"),
]

CUTOFF_HOURS = 48  # include stories from last 48h


def fetch_recent(feed_url, source_name, limit=4):
    try:
        feed = feedparser.parse(feed_url)
    except Exception:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)
    stories = []

    for entry in feed.entries[:20]:
        published = None
        for attr in ("published_parsed", "updated_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    published = datetime(*t[:6], tzinfo=timezone.utc)
                    break
                except Exception:
                    pass

        if published and published < cutoff:
            continue

        title = entry.get("title", "").strip()
        link  = entry.get("link", "").strip()
        if not title:
            continue

        stories.append((title, link))
        if len(stories) >= limit:
            break

    return stories

def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token, chat_id = get_telegram_config()
    today   = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>🤖 AI News Digest - {today}</b>\n"]

    total = 0
    for source_name, feed_url in FEEDS:
        stories = fetch_recent(feed_url, source_name)
        if not stories:
            continue
        lines.append(f"<b> - {source_name} - </b>")
        for title, link in stories:
            if link:
                lines.append(f'• <a href="{link}">{title}</a>')
            else:
                lines.append(f"• {title}")
            total += 1
        lines.append("")

    if total == 0:
        lines.append("No new AI stories in the last 48 hours.")

    message = "\n".join(lines).strip()

    if dry_run:
        print_dry_run(message, f"Would send {total} stories to Telegram")
        return

    send_telegram(message, token, chat_id)
    print(f"Sent {total} stories.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch AI/ML news from RSS feeds and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
