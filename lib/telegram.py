import requests

from .config import BOT_TOKEN


def send_message(text: str, chat_id, parse_mode: str = None) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return True
