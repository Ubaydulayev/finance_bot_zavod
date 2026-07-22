import json
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from . import i18n
from .config import GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID, WS_BUSINESS, WS_EXPENSES, WS_SALARY

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Колонки "Кто внёс" - добавлены в конец каждой таблицы, чтобы не задеть
# существующие данные/формулы (см. i18n-фичу: язык бота + регистрация).
WHO_COL_EXPENSE = 10   # J, "Личные Расходы" - Расход
WHO_COL_INCOME = 11    # K, "Личные Расходы" - Приход
WHO_COL_NAKOPLENIE = 12  # L, "Личные Расходы" - Накопление
WHO_COL_SYRE = 15      # O, "Бизнес" - Сырье
WHO_COL_SVET = 16      # P, "Бизнес" - Свет
WHO_COL_REZKA = 14     # N, "Болларни Ойлиги Обьем" - Обьем ребят за день

_spreadsheet = None
_worksheets = {}


def get_spreadsheet():
    global _spreadsheet
    if _spreadsheet is None:
        info = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        gc = gspread.authorize(creds)
        _spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    return _spreadsheet


def get_worksheet(title: str):
    if title not in _worksheets:
        _worksheets[title] = get_spreadsheet().worksheet(title)
    return _worksheets[title]


def parse_quick_amount(text: str):
    """
    Быстрый ввод без формата:
    - "50000"  -> расход на эту сумму
    - "+50000" -> приход на эту сумму
    Возвращает data-словарь как parse_command, либо None, если это не число.
    """
    stripped = text.strip()

    if stripped.startswith("+"):
        digits = stripped[1:].replace(" ", "")
        if digits.isdigit():
            return {"приход": digits}
        return None

    digits = stripped.replace(" ", "")
    if digits.isdigit():
        return {"расход": digits}
    return None


def parse_positional(text: str, n: int):
    """
    'Тип, з1, з2, ...' -> список из n значений (пустая строка, если не хватает).
    Для команд без подписей Ключ: Значение (Сырье, Свет).
    """
    parts = [p.strip() for p in text.split(",")]
    values = parts[1:1 + n]
    values += [""] * (n - len(values))
    return values


def parse_command(text: str):
    parts = [p.strip() for p in text.split(",")]
    data = {}
    for part in parts:
        if ":" not in part:
            if part:
                data.setdefault("type", part.strip().lower())
            continue
        key, value = part.split(":", 1)
        data[key.strip().lower()] = value.strip()
    return data


def col_letter(n: int) -> str:
    letters = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def find_target_row(ws, name_col: int, amount_col: int):
    """
    Простая версия: ищет по-настоящему пустую строку (обе колонки пустые),
    либо строку с итогами (имя пусто, сумма есть) чтобы вставить над ней.
    Подходит для таблиц, где данные реально пустые в промежутках
    (например "Личные Расходы", "Сырьё").
    """
    col_name = ws.col_values(name_col)
    col_amount = ws.col_values(amount_col)
    max_len = max(len(col_name), len(col_amount))

    for i in range(2, max_len + 2):
        a_val = col_name[i - 1] if i - 1 < len(col_name) else ""
        b_val = col_amount[i - 1] if i - 1 < len(col_amount) else ""
        if not a_val and not b_val:
            return i, "update"
        if not a_val and b_val:
            return i, "insert"

    return max_len + 1, "update"


def find_target_row_by_formula(ws, check_col: int):
    """
    Более надёжная версия для таблиц, где строка с итогами - это ФОРМУЛА
    (например СУММ), а обычные данные - просто числа без формулы.
    Читает колонку в режиме FORMULA, чтобы отличить:
    - пустая ячейка -> сюда можно писать (update)
    - ячейка с формулой (начинается на '=') -> это итоговая строка,
      вставляем новую строку НАД ней (insert)
    - обычное число/текст -> это настоящие данные, идём дальше
    """
    letter = col_letter(check_col)
    values = ws.get(f"{letter}2:{letter}1000", value_render_option="FORMULA")

    for i, row in enumerate(values, start=2):
        cell = str(row[0]).strip() if row else ""
        if cell == "":
            return i, "update"
        if cell.startswith("="):
            return i, "insert"

    return len(values) + 2, "update"


def write_row(ws, row: int, mode: str, start_col: int, values: list):
    end_col = start_col + len(values) - 1
    rng = f"{col_letter(start_col)}{row}:{col_letter(end_col)}{row}"

    if mode == "insert":
        full_row = [""] * (start_col - 1) + values
        ws.insert_row(full_row, index=row)
    else:
        ws.update(rng, [values])


def _write_who(ws, row: int, col: int, who: str):
    if who:
        ws.update(f"{col_letter(col)}{row}", [[who]])


def write_expense(amount: str, category: str, name: str = "", who: str = "", lang: str = "ru") -> str:
    category = category.strip() if category and category.strip() else "Другое"
    today = datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_expenses = get_worksheet(WS_EXPENSES)
        row, mode = find_target_row(sheet_expenses, name_col=1, amount_col=2)
        write_row(sheet_expenses, row, mode, 1, [name, amount, today, category])
        _write_who(sheet_expenses, row, WHO_COL_EXPENSE, who)
        return i18n.t("saved_expense", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def write_income(amount: str, name: str = "", who: str = "", lang: str = "ru") -> str:
    try:
        sheet_expenses = get_worksheet(WS_EXPENSES)
        row, mode = find_target_row(sheet_expenses, name_col=5, amount_col=6)
        write_row(sheet_expenses, row, mode, 5, [name, amount])
        _write_who(sheet_expenses, row, WHO_COL_INCOME, who)
        return i18n.t("saved_income", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def write_rezka(fio: str, date_val: str, m2: str, who: str = "", lang: str = "ru") -> str:
    date_val = date_val.strip() if date_val and date_val.strip() else datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_salary = get_worksheet(WS_SALARY)
        row, mode = find_target_row(sheet_salary, name_col=1, amount_col=2)
        write_row(sheet_salary, row, mode, 1, [date_val, m2])  # A,B (C,D,E - формулы, не трогаем)
        sheet_salary.update(f"F{row}", [[fio]])  # F ФИО
        _write_who(sheet_salary, row, WHO_COL_REZKA, who)
        return i18n.t("saved_rezka", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def write_nakoplenie(amount: str, comment: str = "", who: str = "", lang: str = "ru") -> str:
    today = datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_expenses = get_worksheet(WS_EXPENSES)
        row, mode = find_target_row(sheet_expenses, name_col=7, amount_col=8)
        write_row(sheet_expenses, row, mode, 7, [comment, amount, today])  # G,H,I
        _write_who(sheet_expenses, row, WHO_COL_NAKOPLENIE, who)
        return i18n.t("saved_nakoplenie", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def write_syre(desc: str, cost: str, date_val: str, cubes: str, who: str = "", lang: str = "ru") -> str:
    try:
        sheet_business = get_worksheet(WS_BUSINESS)
        row, mode = find_target_row(sheet_business, name_col=1, amount_col=2)
        write_row(sheet_business, row, mode, 1, [desc, cost, date_val, cubes])  # A,B,C,D
        _write_who(sheet_business, row, WHO_COL_SYRE, who)
        return i18n.t("saved_syre", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def write_svet(date_val: str, reading: str, usage: str, tariff: str, who: str = "", lang: str = "ru") -> str:
    try:
        cost = float(usage) * float(tariff)
    except ValueError:
        cost = ""

    try:
        sheet_business = get_worksheet(WS_BUSINESS)
        row, mode = find_target_row_by_formula(sheet_business, check_col=11)
        write_row(sheet_business, row, mode, 10, [date_val, reading, usage, tariff, cost])
        _write_who(sheet_business, row, WHO_COL_SVET, who)
        return i18n.t("saved_svet", lang, row=row)
    except Exception as e:
        return i18n.t("write_error", lang, error=e)


def handle_expense_message(text: str, who: str = "", lang: str = "ru") -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    first_word = text.split(",", 1)[0].strip().lower()

    # Сырье и Свет вводятся без подписей Ключ: Значение - просто значения по
    # порядку через запятую (Дату можно оставить пустой - подставится сегодня).
    if first_word == "сырье":
        desc, cost, date_val, cubes = parse_positional(text, 4)
        if desc and cost:
            return write_syre(desc, cost, date_val or today, cubes, who=who, lang=lang)
        return i18n.type_template("сырье", lang)

    if first_word == "свет":
        date_val, reading, usage, tariff = parse_positional(text, 4)
        if reading and usage and tariff:
            return write_svet(date_val or today, reading, usage, tariff, who=who, lang=lang)
        return i18n.type_template("свет", lang)

    data = parse_quick_amount(text) or parse_command(text)
    cmd_type = data.get("type", "")
    if cmd_type == "катта":  # старое название команды, оставлено для совместимости
        cmd_type = "резка"

    if cmd_type == "резка" and data.get("м2") and data.get("фио"):
        date_val = data.get("дата", today)
        m2 = data.get("м2", "")
        fio = data.get("фио", "")
        return write_rezka(fio, date_val, m2, who=who, lang=lang)

    elif "расход" in data:
        amount = data["расход"]
        category = data.get("категория", "")
        name = data.get("наименование", "")
        return write_expense(amount, category, name, who=who, lang=lang)

    elif "приход" in data:
        amount = data["приход"]
        name = data.get("наименование", "")
        return write_income(amount, name, who=who, lang=lang)

    elif cmd_type in i18n.TYPE_TEMPLATES:
        # известный тип команды, но без нужных полей - подсказываем точный формат
        return i18n.type_template(cmd_type, lang)

    else:
        return i18n.t("help", lang)
