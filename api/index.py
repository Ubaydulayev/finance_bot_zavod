from flask import Flask, jsonify, request

from lib.config import CRON_SECRET, TELEGRAM_CHAT_ID
from lib.menu import (
    CATEGORY_KEYBOARD,
    CATEGORY_PROMPT_LABEL,
    MAIN_KEYBOARD,
    NAKOPLENIE_PROMPT_LABEL,
    PALIROVKA_KEYBOARD,
    PALIROVKA_PROMPT_LABEL,
    REZKA_KEYBOARD,
    REZKA_PROMPT_LABEL,
    WELCOME_TEXT,
    category_prompt,
    nakoplenie_prompt,
    palirovka_prompt,
    rezka_prompt,
)
from lib.rates import calculate_cross_rates, format_message, get_exchange_rates
from lib.sheets import handle_expense_message, write_expense, write_nakoplenie, write_palirovka, write_rezka
from lib.telegram import answer_callback_query, send_message

app = Flask(__name__)

GREETING_TRIGGERS = {"/start", "/help", "помощь"}
REZKA_TRIGGERS = {"резка", "катта"}  # "катта" оставлено для совместимости со старым названием


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
    text_lower = text.lower()

    if text_lower in GREETING_TRIGGERS:
        send_message(WELCOME_TEXT, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    if text_lower == "расход":
        send_message("Выбери категорию:", chat_id=chat_id, reply_markup=CATEGORY_KEYBOARD)
        return jsonify(ok=True)

    if text_lower in REZKA_TRIGGERS:
        send_message("Выбери, кто делал резку:", chat_id=chat_id, reply_markup=REZKA_KEYBOARD)
        return jsonify(ok=True)

    if text_lower == "палировка":
        send_message("Выбери, кто делал палировку:", chat_id=chat_id, reply_markup=PALIROVKA_KEYBOARD)
        return jsonify(ok=True)

    if text_lower == "накопление":
        send_message(nakoplenie_prompt(), chat_id=chat_id, reply_markup={"force_reply": True})
        return jsonify(ok=True)

    reply_to_text = (message.get("reply_to_message") or {}).get("text", "")

    if reply_to_text.startswith(CATEGORY_PROMPT_LABEL):
        category = reply_to_text.split(CATEGORY_PROMPT_LABEL, 1)[1].splitlines()[0].strip()
        amount, _, name = text.partition(",")
        reply = write_expense(amount.strip(), category, name.strip())
        send_message(reply, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    if reply_to_text.startswith(REZKA_PROMPT_LABEL):
        fio = reply_to_text.split(REZKA_PROMPT_LABEL, 1)[1].splitlines()[0].strip()
        reply = _finish_worker_entry(write_rezka, fio, text)
        send_message(reply, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    if reply_to_text.startswith(PALIROVKA_PROMPT_LABEL):
        fio = reply_to_text.split(PALIROVKA_PROMPT_LABEL, 1)[1].splitlines()[0].strip()
        reply = _finish_worker_entry(write_palirovka, fio, text)
        send_message(reply, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    if reply_to_text.startswith(NAKOPLENIE_PROMPT_LABEL):
        amount, _, comment = text.partition(",")
        reply = write_nakoplenie(amount.strip(), comment.strip())
        send_message(reply, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
        return jsonify(ok=True)

    reply = handle_expense_message(text)
    send_message(reply, chat_id=chat_id)

    return jsonify(ok=True)


def _finish_worker_entry(write_fn, fio: str, text: str) -> str:
    """
    Достраивает запись Резки/Палировки после того, как ФИО уже выбрано кнопкой.
    Если ФИО было "Другое" - ждём "ФИО, Дата, м2" (или "ФИО, м2").
    Иначе ждём "Дата, м2" (или просто "м2").
    """
    parts = [p.strip() for p in text.split(",")]

    if fio == "Другое":
        if len(parts) >= 3:
            fio, date_val, m2 = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            fio, date_val, m2 = parts[0], "", parts[1]
        else:
            return "Нужно ФИО и м2 через запятую, например: Расим, 150"
    elif len(parts) >= 2:
        date_val, m2 = parts[0], parts[1]
    else:
        date_val, m2 = "", parts[0]

    return write_fn(fio, date_val, m2)


def handle_callback(callback):
    data = callback.get("data", "")
    chat_id = callback["message"]["chat"]["id"]

    if data.startswith("cat:"):
        category = data[len("cat:"):]
        answer_callback_query(callback["id"])
        send_message(category_prompt(category), chat_id=chat_id, reply_markup={"force_reply": True})

    elif data.startswith("rezka:"):
        fio = data[len("rezka:"):]
        answer_callback_query(callback["id"])
        send_message(rezka_prompt(fio), chat_id=chat_id, reply_markup={"force_reply": True})

    elif data.startswith("pal:"):
        fio = data[len("pal:"):]
        answer_callback_query(callback["id"])
        send_message(palirovka_prompt(fio), chat_id=chat_id, reply_markup={"force_reply": True})

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
