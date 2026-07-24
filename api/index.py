from flask import Flask, jsonify, request

from lib import i18n, users
from lib.config import CRON_SECRET
from lib.menu import CATEGORY_KEYBOARD, REPORT_KEYBOARD, REZKA_KEYBOARD, category_prompt, nakoplenie_prompt, rezka_prompt
from lib.rates import calculate_cross_rates, format_message, get_exchange_rates
from lib.sheets import get_report, handle_expense_message, write_expense, write_nakoplenie, write_rezka
from lib.telegram import answer_callback_query, send_message

app = Flask(__name__)

SLASH_HELP = {"/start", "/help"}
SLASH_LANGUAGE = {"/language", "/язык", "/til"}

# action-код -> ключ в TYPE_TEMPLATES, для кнопок без своего интерактивного флоу
ACTION_TO_TEMPLATE_KEY = {
    "income": "приход",
    "syre": "сырье",
    "svet": "свет",
}


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    callback = update.get("callback_query")
    if callback:
        return handle_callback(callback)

    message = update.get("message") or update.get("edited_message")
    if not message:
        return jsonify(ok=True)

    chat_id = message["chat"]["id"]

    # ===== 1) РЕГИСТРАЦИЯ: язык -> телефон -> имя =====
    user = users.find_user(chat_id)

    if user is None:
        send_message(i18n.t("ask_language", i18n.DEFAULT_LANG), chat_id=chat_id, reply_markup=i18n.language_keyboard())
        return jsonify(ok=True)

    lang = user["lang"]

    if not user.get("phone"):
        contact = message.get("contact")
        sender_id = (message.get("from") or {}).get("id")
        if contact and contact.get("phone_number") and contact.get("user_id") == sender_id:
            users.set_phone(user, contact["phone_number"])
            send_message(
                f"{i18n.ASK_NAME_LABEL[lang]}\n{i18n.t('ask_name_prompt', lang)}",
                chat_id=chat_id, reply_markup={"force_reply": True},
            )
        else:
            send_message(i18n.t("ask_contact_reminder", lang), chat_id=chat_id, reply_markup=i18n.contact_keyboard(lang))
        return jsonify(ok=True)

    if not user.get("name"):
        text = (message.get("text") or "").strip()
        reply_to_text = (message.get("reply_to_message") or {}).get("text", "")
        prompt_type, _, _ = i18n.match_prompt(reply_to_text)
        if prompt_type == "name" and text:
            users.set_name(user, text)
            send_message(i18n.t("registered_done", lang, name=text), chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        else:
            send_message(
                f"{i18n.ASK_NAME_LABEL[lang]}\n{i18n.t('ask_name_prompt', lang)}",
                chat_id=chat_id, reply_markup={"force_reply": True},
            )
        return jsonify(ok=True)

    # ===== 2) Пользователь полностью зарегистрирован =====
    who = user["name"]

    if "text" not in message:
        return jsonify(ok=True)

    text = message["text"].strip()
    text_lower = text.lower()
    action = i18n.ACTION_BY_LABEL.get(text_lower)

    if text_lower in SLASH_HELP or action == "help":
        send_message(i18n.t("welcome", lang), chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        return jsonify(ok=True)

    if text_lower in SLASH_LANGUAGE or action == "language":
        send_message(i18n.t("ask_language", lang), chat_id=chat_id, reply_markup=i18n.language_keyboard())
        return jsonify(ok=True)

    if action == "expense":
        send_message(i18n.t("category_choose", lang), chat_id=chat_id, reply_markup=CATEGORY_KEYBOARD)
        return jsonify(ok=True)

    if action == "rezka":
        send_message(i18n.t("rezka_choose", lang), chat_id=chat_id, reply_markup=REZKA_KEYBOARD)
        return jsonify(ok=True)

    if action == "nakoplenie":
        send_message(nakoplenie_prompt(lang), chat_id=chat_id, reply_markup={"force_reply": True})
        return jsonify(ok=True)

    if action == "report":
        send_message(i18n.t("report_choose", lang), chat_id=chat_id, reply_markup=REPORT_KEYBOARD)
        return jsonify(ok=True)

    if action in ACTION_TO_TEMPLATE_KEY:
        send_message(i18n.type_template(ACTION_TO_TEMPLATE_KEY[action], lang), chat_id=chat_id)
        return jsonify(ok=True)

    reply_to_text = (message.get("reply_to_message") or {}).get("text", "")
    prompt_type, label, _ = i18n.match_prompt(reply_to_text)

    if prompt_type == "category":
        category = reply_to_text.split(label, 1)[1].splitlines()[0].strip()
        amount, _, name = text.partition(",")
        reply = write_expense(amount.strip(), category, name.strip(), who=who, lang=lang)
        send_message(reply, chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        return jsonify(ok=True)

    if prompt_type == "rezka":
        fio = reply_to_text.split(label, 1)[1].splitlines()[0].strip()
        reply = _finish_worker_entry(write_rezka, fio, text, who, lang)
        send_message(reply, chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        return jsonify(ok=True)

    if prompt_type == "nakoplenie":
        amount, _, comment = text.partition(",")
        reply = write_nakoplenie(amount.strip(), comment.strip(), who=who, lang=lang)
        send_message(reply, chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        return jsonify(ok=True)

    reply = handle_expense_message(text, who=who, lang=lang)
    send_message(reply, chat_id=chat_id)

    return jsonify(ok=True)


def _finish_worker_entry(write_fn, fio: str, text: str, who: str, lang: str) -> str:
    """
    Достраивает запись объёма после того, как ФИО уже выбрано кнопкой.
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
            return i18n.t("worker_entry_hint", lang)
    elif len(parts) >= 2:
        date_val, m2 = parts[0], parts[1]
    else:
        date_val, m2 = "", parts[0]

    return write_fn(fio, date_val, m2, who=who, lang=lang)


def handle_callback(callback):
    data = callback.get("data", "")
    chat_id = callback["message"]["chat"]["id"]

    if data.startswith("lang:"):
        lang = data[len("lang:"):]
        answer_callback_query(callback["id"])
        existing = users.find_user(chat_id)

        if existing is None:
            users.create_user_with_lang(chat_id, lang)
            send_message(i18n.t("ask_contact", lang), chat_id=chat_id, reply_markup=i18n.contact_keyboard(lang))
        elif not users.is_fully_registered(existing):
            users.set_lang(existing, lang)
            if not existing.get("phone"):
                send_message(i18n.t("ask_contact", lang), chat_id=chat_id, reply_markup=i18n.contact_keyboard(lang))
            else:
                send_message(
                    f"{i18n.ASK_NAME_LABEL[lang]}\n{i18n.t('ask_name_prompt', lang)}",
                    chat_id=chat_id, reply_markup={"force_reply": True},
                )
        else:
            users.set_lang(existing, lang)
            send_message(i18n.t("language_changed", lang), chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))
        return jsonify(ok=True)

    user = users.find_user(chat_id)
    lang = user["lang"] if user else i18n.DEFAULT_LANG

    if data.startswith("cat:"):
        category = data[len("cat:"):]
        answer_callback_query(callback["id"])
        send_message(category_prompt(category, lang), chat_id=chat_id, reply_markup={"force_reply": True})

    elif data.startswith("rezka:"):
        fio = data[len("rezka:"):]
        answer_callback_query(callback["id"])
        send_message(rezka_prompt(fio, lang), chat_id=chat_id, reply_markup={"force_reply": True})

    elif data.startswith("rep:"):
        key = data[len("rep:"):]
        answer_callback_query(callback["id"])
        reply = get_report(key, lang)
        send_message(reply, chat_id=chat_id, reply_markup=i18n.main_keyboard(lang))

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

    sent, failed = 0, 0
    for u in users.list_users():
        try:
            send_message(message, chat_id=u["chat_id"], parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    return jsonify(ok=True, sent=sent, failed=failed)
