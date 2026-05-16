import feedparser
import requests
import os
from datetime import date, datetime, timezone, timedelta

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
        # try to parse published date
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
    token   = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
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

    # Telegram max message length is 4096 chars
    if len(message) > 4000:
        message = message[:4000] + "\n\n<i>…truncated</i>"

    send_telegram(message, token, chat_id)
    print(f"Sent {total} stories.")


if __name__ == "__main__":
    main()
