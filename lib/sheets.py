import json
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from .config import GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID, WS_BUSINESS, WS_EXPENSES, WS_SALARY
from .menu import HELP_TEXT, TYPE_TEMPLATES

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

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


def write_expense(amount: str, category: str, name: str = "") -> str:
    category = category.strip() if category and category.strip() else "Другое"
    today = datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_expenses = get_worksheet(WS_EXPENSES)
        row, mode = find_target_row(sheet_expenses, name_col=1, amount_col=2)
        write_row(sheet_expenses, row, mode, 1, [name, amount, today, category])
        return f"Расход записан (строка {row})"
    except Exception as e:
        return f"Ошибка при записи в таблицу: {e}"


def write_rezka(fio: str, date_val: str, m2: str) -> str:
    date_val = date_val.strip() if date_val and date_val.strip() else datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_salary = get_worksheet(WS_SALARY)
        row, mode = find_target_row(sheet_salary, name_col=1, amount_col=2)
        write_row(sheet_salary, row, mode, 1, [date_val, m2])  # A,B (C,D,E - формулы, не трогаем)
        sheet_salary.update(f"F{row}", [[fio]])  # F ФИО
        return f"Резка записана (строка {row})"
    except Exception as e:
        return f"Ошибка при записи в таблицу: {e}"


def write_palirovka(fio: str, date_val: str, m2: str) -> str:
    date_val = date_val.strip() if date_val and date_val.strip() else datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_salary = get_worksheet(WS_SALARY)
        row, mode = find_target_row_by_formula(sheet_salary, check_col=10)
        write_row(sheet_salary, row, mode, 8, [fio, date_val, m2])  # H,I,J (K,L,M - формулы)
        return f"Палировка записана (строка {row})"
    except Exception as e:
        return f"Ошибка при записи в таблицу: {e}"


def write_nakoplenie(amount: str, comment: str = "") -> str:
    today = datetime.now().strftime("%d.%m.%Y")

    try:
        sheet_expenses = get_worksheet(WS_EXPENSES)
        row, mode = find_target_row(sheet_expenses, name_col=7, amount_col=8)
        write_row(sheet_expenses, row, mode, 7, [comment, amount, today])  # G,H,I
        return f"Накопление записано (строка {row})"
    except Exception as e:
        return f"Ошибка при записи в таблицу: {e}"


def handle_expense_message(text: str) -> str:
    data = parse_quick_amount(text) or parse_command(text)
    today = datetime.now().strftime("%d.%m.%Y")
    cmd_type = data.get("type", "")
    if cmd_type == "катта":  # старое название команды, оставлено для совместимости
        cmd_type = "резка"

    try:
        if cmd_type == "резка" and data.get("м2") and data.get("фио"):
            date_val = data.get("дата", today)
            m2 = data.get("м2", "")
            fio = data.get("фио", "")
            return write_rezka(fio, date_val, m2)

        elif cmd_type == "палировка" and data.get("фио") and data.get("м2"):
            fio = data.get("фио", "")
            date_val = data.get("дата", today)
            m2 = data.get("м2", "")
            return write_palirovka(fio, date_val, m2)

        elif cmd_type == "сырье" and data.get("описание") and data.get("стоимость"):
            desc = data.get("описание", "")
            cost = data.get("стоимость", "")
            date_val = data.get("дата", today)
            cubes = data.get("кубы", "")

            sheet_business = get_worksheet(WS_BUSINESS)
            row, mode = find_target_row(sheet_business, name_col=1, amount_col=2)
            write_row(sheet_business, row, mode, 1, [desc, cost, date_val, cubes])  # A,B,C,D
            return f"Приход сырья записан (строка {row})"

        elif cmd_type == "свет" and data.get("показание") and data.get("расход") and data.get("тариф"):
            date_val = data.get("дата", today)
            reading = data.get("показание", "")
            usage = data.get("расход", "")
            tariff = data.get("тариф", "")

            try:
                cost = float(usage) * float(tariff)
            except ValueError:
                cost = ""

            sheet_business = get_worksheet(WS_BUSINESS)
            row, mode = find_target_row_by_formula(sheet_business, check_col=11)
            write_row(sheet_business, row, mode, 10, [date_val, reading, usage, tariff, cost])
            return f"Расход света записан (строка {row})"

        elif "расход" in data:
            amount = data["расход"]
            category = data.get("категория", "")
            name = data.get("наименование", "")
            return write_expense(amount, category, name)

        elif "приход" in data:
            amount = data["приход"]
            name = data.get("наименование", "")
            sheet_expenses = get_worksheet(WS_EXPENSES)
            row, mode = find_target_row(sheet_expenses, name_col=5, amount_col=6)
            write_row(sheet_expenses, row, mode, 5, [name, amount])
            return f"Приход записан (строка {row})"

        elif cmd_type in TYPE_TEMPLATES:
            # известный тип команды, но без нужных полей - подсказываем точный формат
            return TYPE_TEMPLATES[cmd_type]

        else:
            return HELP_TEXT

    except Exception as e:
        return f"Ошибка при записи в таблицу: {e}"
