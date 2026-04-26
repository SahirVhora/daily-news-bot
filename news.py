import feedparser
import requests
import os
from datetime import date
from html.parser import HTMLParser

def fetch_bbc_news():
    feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
    stories = []
    for entry in feed.entries[:10]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        stories.append((title, summary, link))
    return stories

def fetch_x_trends():
    class TrendParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_trend = False
            self.trends = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "a" and "trend-link" in attrs.get("class", ""):
                self.in_trend = True
        def handle_data(self, data):
            if self.in_trend:
                self.trends.append(data.strip())
                self.in_trend = False

    headers = {"User-Agent": "Mozilla/5.0 (compatible; newsbot/1.0)"}
    resp = requests.get("https://trends24.in/united-kingdom/", headers=headers, timeout=10)
    resp.raise_for_status()
    p = TrendParser()
    p.feed(resp.text)
    return p.trends[:10]

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
    trends = fetch_x_trends()
    today = date.today().strftime("%A, %d %B %Y")

    # BBC News section
    lines = [f"<b>Top 10 News — {today}</b>\n"]
    for i, (title, summary, link) in enumerate(stories, 1):
        lines.append(f"<b>{i}. {title}</b>")
        if summary:
            lines.append(summary)
        if link:
            lines.append(f'<a href="{link}">Read more</a>')
        lines.append("")

    # X Trends section
    lines.append("─" * 20)
    lines.append(f'\n<b>Top 10 Trending on X (UK) — {today}</b>\n')
    for i, trend in enumerate(trends, 1):
        search_url = f"https://x.com/search?q={requests.utils.quote(trend)}&src=trend_click"
        lines.append(f'{i}. <a href="{search_url}">{trend}</a>')

    message = "\n".join(lines).strip()
    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    main()
