from flask import Flask, jsonify, request

from lib.config import CRON_SECRET, TELEGRAM_CHAT_ID
from lib.rates import calculate_cross_rates, format_message, get_exchange_rates
from lib.sheets import handle_expense_message
from lib.telegram import send_message

app = Flask(__name__)


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message")

    if not message or "text" not in message:
        return jsonify(ok=True)

    chat_id = message["chat"]["id"]
    text = message["text"]

    reply = handle_expense_message(text)
    send_message(reply, chat_id=chat_id)

    return jsonify(ok=True)


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
