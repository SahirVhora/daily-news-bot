import feedparser
import os
from datetime import date

from digest_common import get_telegram_config, print_dry_run, send_telegram

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

def main(dry_run=False):
    if dry_run:
        print("[DRY RUN] Would fetch news and send to Telegram\n")
    token, chat_id = get_telegram_config()

    stories = fetch_sap_news()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>🔵 SAP / SuccessFactors News - {today}</b>\n"]

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

    message = "\n".join(lines).strip()

    if dry_run:
        print_dry_run(message, f"Would send {len(stories)} SAP stories to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent successfully.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch SAP/SuccessFactors news and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
