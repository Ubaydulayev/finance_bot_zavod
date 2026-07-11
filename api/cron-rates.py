from flask import Flask, jsonify, request

from lib.config import CRON_SECRET, TELEGRAM_CHAT_ID
from lib.rates import calculate_cross_rates, format_message, get_exchange_rates
from lib.telegram import send_message

app = Flask(__name__)


@app.route("/api/cron-rates", methods=["GET"])
def cron_rates():
    if CRON_SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {CRON_SECRET}":
            return jsonify(ok=False, error="unauthorized"), 401

    rates, timestamp = get_exchange_rates()
    if not rates or not all(rates.values()):
        return jsonify(ok=False, error="rates unavailable"), 502

    cross_rates = calculate_cross_rates(rates["USD_UZS"], rates["USD_RUB"], rates["USD_EUR"])
    message = format_message(rates, timestamp, cross_rates)

    send_message(message, chat_id=TELEGRAM_CHAT_ID, parse_mode="Markdown")

    return jsonify(ok=True)
