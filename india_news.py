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
    today = date.today().strftime("%A, %d %B %Y")

    stories = fetch_news("https://feeds.feedburner.com/ndtvnews-top-stories")
    lines = [f"<b>🇮🇳 Top 10 India News - {today}</b>\n"]
    for i, (title, summary, link) in enumerate(stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f'<a href="{link}">Read more</a>')
        lines.append("")
    send_telegram("\n".join(lines).strip(), token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    main()
