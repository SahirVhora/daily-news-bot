import os
from typing import Iterable

import requests

TELEGRAM_MAX_LENGTH = 4000


def get_telegram_config() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def split_message(message: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    if len(message) <= max_length:
        return [message]

    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in message.splitlines():
        addition = len(line) + (1 if current else 0)
        if current and current_len + addition > max_length:
            parts.append("\n".join(current))
            current = [line]
            current_len = len(line)
            continue
        current.append(line)
        current_len += addition

    if current:
        parts.append("\n".join(current))
    return parts


def send_telegram(
    message: str,
    token: str,
    chat_id: str,
    *,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
    timeout: int = 15,
) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for part in split_message(message):
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()


def print_dry_run(message: str, *details: str) -> None:
    print(message)
    print(f"\n[DRY RUN] Message parts: {len(split_message(message))}")
    for detail in details:
        print(f"[DRY RUN] {detail}")

