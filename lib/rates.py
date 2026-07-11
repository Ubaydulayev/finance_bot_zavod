import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


def get_exchange_rates():
    """
    Получает текущие курсы USD/UZS, USD/RUB и USD/EUR
    """
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        rates = {
            "USD_UZS": data["rates"].get("UZS"),
            "USD_RUB": data["rates"].get("RUB"),
            "USD_EUR": data["rates"].get("EUR"),
        }

        return rates, data["time_last_updated"]

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении данных о курсах: {e}")
        return None, None


def calculate_cross_rates(usd_uzs, usd_rub, usd_eur):
    """
    Вычисляет кросс-курсы на основе курсов к USD
    """
    return {
        "RUB_to_UZS": usd_uzs / usd_rub,
        "UZS_to_RUB": usd_rub / usd_uzs,
        "UZS_to_EUR": usd_eur / usd_uzs,
        "EUR_to_UZS": usd_uzs / usd_eur,
        "RUB_to_EUR": usd_eur / usd_rub,
        "EUR_to_RUB": usd_rub / usd_eur,
    }


def format_message(rates, timestamp, cross_rates):
    """
    Форматирует сообщение для Telegram
    """
    usd_uzs = rates["USD_UZS"]
    usd_rub = rates["USD_RUB"]
    usd_eur = rates["USD_EUR"]

    if isinstance(timestamp, int):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    time_str = dt.strftime("%d.%m.%Y %H:%M:%S")

    message = f"""
📊 *КУРСЫ ВАЛЮТ* 💱
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Обновлено: {time_str}

*Основные курсы к USD:*
• 1 USD = {usd_uzs:,.2f} UZS
• 1 USD = {usd_rub:,.2f} RUB
• 1 USD = {usd_eur:,.4f} EUR

*Кросс-курсы:*
• 1 RUB = {cross_rates['RUB_to_UZS']:,.2f} UZS
• 1 EUR = {cross_rates['EUR_to_UZS']:,.2f} UZS
• 1 EUR = {cross_rates['EUR_to_RUB']:,.2f} RUB
• 1 RUB = {cross_rates['RUB_to_EUR']:,.4f} EUR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Данные получены автоматически
"""

    return message.strip()
