import feedparser
import requests
import os
from datetime import date

def fetch_news(feed_url, limit=10):
    feed = feedparser.parse(feed_url)
    stories = []
    for entry in feed.entries[:limit]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        stories.append((title, summary, link))
    return stories

def send_telegram(message, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    uk_stories = fetch_news("http://feeds.bbci.co.uk/news/rss.xml")
    india_stories = fetch_news("https://feeds.feedburner.com/ndtvnews-top-stories")

    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>Daily News — {today}</b>\n"]

    # UK News
    lines.append("<b>🇬🇧 Top 10 UK News</b>\n")
    for i, (title, summary, link) in enumerate(uk_stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f'<a href="{link}">Read more</a>')
        lines.append("")

    lines.append("─" * 20)
    lines.append("")

    # India News
    lines.append("<b>🇮🇳 Top 10 India News</b>\n")
    for i, (title, summary, link) in enumerate(india_stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f'<a href="{link}">Read more</a>')
        lines.append("")

    message = "\n".join(lines).strip()
    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    main()
