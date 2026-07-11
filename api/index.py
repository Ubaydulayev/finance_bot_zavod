from flask import Flask, jsonify, request

from lib.config import CRON_SECRET, TELEGRAM_CHAT_ID
from lib.menu import CATEGORY_KEYBOARD, CATEGORY_PROMPT_LABEL, MAIN_KEYBOARD, WELCOME_TEXT, category_prompt
from lib.rates import calculate_cross_rates, format_message, get_exchange_rates
from lib.sheets import handle_expense_message, write_expense
from lib.telegram import answer_callback_query, send_message

app = Flask(__name__)

GREETING_TRIGGERS = {"/start", "/help", "помощь"}


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    callback = update.get("callback_query")
    if callback:
        return handle_callback(callback)

    message = update.get("message") or update.get("edited_message")

    if not message or "text" not in message:
        return jsonify(ok=True)

    chat_id = message["chat"]["id"]
    text = message["text"].strip()

    if text.lower() in GREETING_TRIGGERS:
        send_message(WELCOME_TEXT, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    if text.lower() == "расход":
        send_message("Выбери категорию:", chat_id=chat_id, reply_markup=CATEGORY_KEYBOARD)
        return jsonify(ok=True)

    reply_to = message.get("reply_to_message") or {}
    if reply_to.get("text", "").startswith(CATEGORY_PROMPT_LABEL):
        category = reply_to["text"].split(CATEGORY_PROMPT_LABEL, 1)[1].splitlines()[0].strip()
        amount, _, name = text.partition(",")
        reply = write_expense(amount.strip(), category, name.strip())
        send_message(reply, chat_id=chat_id)
        return jsonify(ok=True)

    reply = handle_expense_message(text)
    send_message(reply, chat_id=chat_id)

    return jsonify(ok=True)


def handle_callback(callback):
    data = callback.get("data", "")
    chat_id = callback["message"]["chat"]["id"]

    if data.startswith("cat:"):
        category = data[len("cat:"):]
        answer_callback_query(callback["id"])
        send_message(category_prompt(category), chat_id=chat_id, reply_markup={"force_reply": True})

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
