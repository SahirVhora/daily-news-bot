import feedparser
import requests
import os
from datetime import date

SAP_FEEDS = [
    ("SAP News", "https://news.sap.com/feed/"),
    ("Google News: SuccessFactors", "https://news.google.com/rss/search?q=SAP+SuccessFactors&hl=en-GB&gl=GB&ceid=GB:en"),
    ("Google News: SAP HR", "https://news.google.com/rss/search?q=SAP+HCM+OR+SAP+HR+transformation&hl=en-GB&gl=GB&ceid=GB:en"),
]

SAP_KEYWORDS = [
    "successfactors", "success factors", "sap hcm", "sap hr",
    "s/4hana", "sap btp", "hxm", "employee central",
    "workforce", "payroll", "talent management", "sap"
]

def fetch_sap_news(limit=10):
    seen = set()
    stories = []
    for source, url in SAP_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                text = (title + " " + summary).lower()
                if any(kw in text for kw in SAP_KEYWORDS):
                    if link not in seen:
                        seen.add(link)
                        stories.append((source, title, summary[:200] if summary else "", link))
            if len(stories) >= limit:
                break
        except Exception:
            continue
    return stories[:limit]

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

    stories = fetch_sap_news()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>🔵 SAP / SuccessFactors News — {today}</b>\n"]

    if not stories:
        lines.append("No SAP news found today.")
    else:
        for i, (source, title, summary, link) in enumerate(stories, 1):
            lines.append(f"<b>{i}. {title}</b>")
            lines.append(f"<i>{source}</i>")
            if summary:
                lines.append(summary)
            if link:
                lines.append(f'<a href="{link}">Read more</a>')
            lines.append("")

    send_telegram("\n".join(lines).strip(), token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    main()
