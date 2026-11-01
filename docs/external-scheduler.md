# External scheduler

GitHub Actions `schedule` jobs can be delayed, so Telegram digests are
dispatched by an external scheduler using the GitHub Actions dispatch API.

## Request

Create one `POST` job per row below. Use the scheduler's secret/header store
for the fine-grained GitHub token - never put it in a URL or request body.

```
URL: https://api.github.com/repos/SahirVhora/daily-news-bot/actions/workflows/digests.yml/dispatches
Headers:
  Accept: application/vnd.github+json
  X-GitHub-Api-Version: 2022-11-28
  Authorization: Bearer <SCHEDULER_GITHUB_TOKEN>
Body: {"ref":"main","inputs":{"digest":"<digest_id>"}}
```

The token must be a fine-grained personal access token restricted to this
repository with **Actions: write** permission. Store it only in the scheduler.

## Schedules

All schedules are UTC.

| Digest ID | Cron | Intended time |
| --- | --- | --- |
| `github_triage_digest` | `0 0 * * *` | Daily 00:00 |
| `uk_news` | `15 6 * * *` | Daily 06:15 |
| `india_news` | `25 6 * * *` | Daily 06:25 |
| `sap_news` | `35 6 * * *` | Daily 06:35 |
| `github_trending` | `45 6 * * *` | Daily 06:45 |
| `x_trends` | `45 6 * * *` | Daily 06:45 |
| `top_news` | `0 7 * * *` | Daily 07:00 |
| `ai_news` | `10 7 * * *` | Daily 07:10 |
| `github_health_digest` | `0 8 * * 0` | Sunday 08:00 |

After changing a job, use the scheduler's one-off test facility with a
non-production test digest only if one is available. A normal dispatch sends
a real Telegram message.