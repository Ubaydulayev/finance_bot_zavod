from flask import Flask, jsonify, request

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
