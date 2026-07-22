from datetime import datetime

from .config import GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID
from .i18n import DEFAULT_LANG

WS_USERS = "Пользователи"
_HEADER = ["chat_id", "Имя", "Телефон", "Язык", "Дата регистрации"]

_users_ws = None


def get_users_ws():
    global _users_ws
    if _users_ws is not None:
        return _users_ws

    from .sheets import get_spreadsheet  # локальный импорт, чтобы не плодить циклы

    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(WS_USERS)
    except Exception:
        ws = spreadsheet.add_worksheet(title=WS_USERS, rows=500, cols=len(_HEADER))
        ws.update("A1", [_HEADER])

    _users_ws = ws
    return ws


def _row_to_user(row_num: int, row: list) -> dict:
    row = row + [""] * (len(_HEADER) - len(row))
    return {
        "row": row_num,
        "chat_id": row[0],
        "name": row[1],
        "phone": row[2],
        "lang": row[3] or DEFAULT_LANG,
        "registered_at": row[4],
    }


def find_user(chat_id) -> dict | None:
    ws = get_users_ws()
    col = ws.col_values(1)
    chat_id = str(chat_id)
    for i, value in enumerate(col[1:], start=2):
        if value == chat_id:
            row = ws.get(f"A{i}:E{i}")
            return _row_to_user(i, row[0] if row else [chat_id])
    return None


def is_fully_registered(user: dict | None) -> bool:
    return bool(user and user.get("name") and user.get("phone") and user.get("lang"))


def create_user_with_lang(chat_id, lang: str) -> dict:
    ws = get_users_ws()
    today = datetime.now().strftime("%d.%m.%Y")
    ws.append_row([str(chat_id), "", "", lang, today])
    user = find_user(chat_id)
    return user


def set_phone(user: dict, phone: str):
    ws = get_users_ws()
    ws.update(f"C{user['row']}", [[phone]])


def set_name(user: dict, name: str):
    ws = get_users_ws()
    ws.update(f"B{user['row']}", [[name]])


def set_lang(user: dict, lang: str):
    ws = get_users_ws()
    ws.update(f"D{user['row']}", [[lang]])
