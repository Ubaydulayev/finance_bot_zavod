from . import i18n

# Реальные категории расходов из таблицы "Личные Расходы" + "Другое"
# Названия НЕ переводятся - привязаны к dropdown-списку колонки D в таблице.
EXPENSE_CATEGORIES = [
    "Завтрак", "Обед", "Ужин", "Питание",
    "Такси", "Пропан", "Салярка кара учун",
    "Сегмент", "Шарожка", "Йолкира блок",
    "Сырье", "Ойлик", "Ехсон",
    "Другое",
]

# ФИО рабочих для Резки и Палировки (общий список, редактируется по запросу)
FIO_LIST = ["Нодир", "Исмат", "Шахоб", "Фазлиддин", "Зафар", "Курбон", "Вали", "Другое"]


def _keyboard(items, callback_prefix, per_row=2):
    rows, row = [], []
    for item in items:
        row.append({"text": item, "callback_data": f"{callback_prefix}:{item}"})
        if len(row) == per_row:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return {"inline_keyboard": rows}


CATEGORY_KEYBOARD = _keyboard(EXPENSE_CATEGORIES, "cat", per_row=2)
REZKA_KEYBOARD = _keyboard(FIO_LIST, "rezka", per_row=3)
PALIROVKA_KEYBOARD = _keyboard(FIO_LIST, "pal", per_row=3)


def category_prompt(category: str, lang: str) -> str:
    return i18n.t("category_prompt", lang, category=category)


def rezka_prompt(fio: str, lang: str) -> str:
    if fio == "Другое":
        return i18n.t("rezka_prompt_other", lang)
    return i18n.t("rezka_prompt", lang, fio=fio)


def palirovka_prompt(fio: str, lang: str) -> str:
    if fio == "Другое":
        return i18n.t("palirovka_prompt_other", lang)
    return i18n.t("palirovka_prompt", lang, fio=fio)


def nakoplenie_prompt(lang: str) -> str:
    return i18n.t("nakoplenie_prompt", lang)
