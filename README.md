<img src="https://sahirvhora.github.io/daily-news-bot/preview.svg" width="0" height="0" alt="" style="display:none">

# Daily News Bot

Multi-source news digest delivered to Telegram via GitHub Actions. Covers UK news, India news, AI/ML, SAP/SuccessFactors, GitHub trending, global top stories, and precious metals prices.

## Feeds

| Script | Source | Content |
|--------|--------|---------|
| `news.py` | BBC + NDTV RSS | UK & India top 10 headlines |
| `top_news.py` | BBC category feeds | World, UK, Tech, Business, Science |
| `ai_news.py` | 6 AI RSS feeds | AI/ML news from Verge, MIT, VentureBeat, DeepMind, OpenAI, HuggingFace |
| `sap_news.py` | SAP + Google News | SAP SuccessFactors & HR transformation |
| `github_trending.py` | GitHub Trending | Top 10 trending repos daily |
| `india_news.py` | NDTV RSS | India-specific top stories |
| `metal_alert.py` | Yahoo Finance | Gold & Silver prices in GBP (hourly) |

## Setup

```bash
pip install -r requirements.txt
```

Set environment variables:
- `TELEGRAM_BOT_TOKEN` - your Telegram bot token
- `TELEGRAM_CHAT_ID` - target chat/channel ID

## Usage

```bash
python3 top_news.py
python3 ai_news.py
python3 metal_alert.py
```

## Automation

Runs on GitHub Actions schedule. See `.github/workflows/` for cron configuration.
