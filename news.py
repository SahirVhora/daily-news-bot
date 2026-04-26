import feedparser
import requests
import os
from datetime import date

def fetch_bbc_news():
    feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
    stories = []
    for entry in feed.entries[:10]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        stories.append((title, summary))
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

    stories = fetch_bbc_news()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>Top 10 News — {today}</b>\n"]
    for i, (title, summary) in enumerate(stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        lines.append("")

    message = "\n".join(lines).strip()
    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    main()
