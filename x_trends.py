"""
x_trends.py - Fetches trending topics via Google Trends RSS (UK + Worldwide)
and sends a daily digest to Telegram.
Uses only stdlib + requests - no external feedparser needed.
Runs via GitHub Actions on a schedule.
"""

import os
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

from digest_common import get_telegram_config, print_dry_run, send_telegram

FEEDS = [
    ("UK Trends", "https://trends.google.com/trending/rss?geo=GB", "🇬🇧"),
    ("Worldwide Trends", "https://trends.google.com/trending/rss", "🌍"),
]

NS = {"ht": "https://trends.google.com/trending/rss"}


def fetch_trends(url, limit=10):
    """Parse Google Trends RSS and return list of (title, traffic, link) tuples."""
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = resp.read().decode("utf-8")
        root = ET.fromstring(data)
        trends = []
        for item in root.findall(".//item")[:limit]:
            title_el = item.find("title")
            link_el = item.find("link")
            traffic_el = item.find("ht:approx_traffic", NS)
            title = html.escape(title_el.text.strip()) if title_el is not None and title_el.text else ""
            link = link_el.text.strip() if link_el is not None and link_el.text else ""
            traffic = traffic_el.text.strip() if traffic_el is not None and traffic_el.text else ""
            if title:
                trends.append((title, traffic, link))
        return trends
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def main(dry_run=False):
    token, chat_id = get_telegram_config()
    today = date.today().strftime("%A, %d %B %Y")

    lines = [f"<b>🔥 Daily Trending Topics - {today}</b>\n"]

    for section, url, emoji in FEEDS:
        trends = fetch_trends(url, limit=10)
        if not trends:
            lines.append(f"\n<b>{emoji} {section}</b>")
            lines.append("  (no data available)")
            continue
        lines.append(f"\n<b>{emoji} {section}</b>")
        for i, (title, traffic, link) in enumerate(trends, 1):
            traffic_str = f" ({traffic})" if traffic else ""
            if link:
                lines.append(f'{i}. <a href="{link}">{title}</a>{traffic_str}')
            else:
                lines.append(f"{i}. {title}{traffic_str}")

    lines.append("\n<i>Source: Google Trends RSS • Runs daily at 7:45 AM UTC</i>")

    message = "\n".join(lines)

    if dry_run:
        total = sum(1 for line in lines if line.startswith(tuple(str(i) for i in range(1, 10))) or line.startswith("10."))
        print_dry_run(message, f"Would send approximately {total} trends to Telegram")
        return

    send_telegram(message, token, chat_id)
    print("Sent X trends digest to Telegram.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fetch trending topics and send to Telegram")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of sending")
    args = p.parse_args()
    main(dry_run=args.dry_run)
