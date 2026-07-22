"""
Переводы (RU/UZ) для всех текстов бота.
Названия категорий расходов и ФИО работников НЕ переводятся —
они жёстко привязаны к спискам в самой Google Таблице (dropdown колонки D,
список ФИО), перевод сломал бы группировку/фильтры там.
"""

LANGS = ("ru", "uz")
DEFAULT_LANG = "ru"

LANG_LABELS = {"ru": "🇷🇺 Русский", "uz": "🇺🇿 O'zbekcha"}

# action-код -> подпись кнопки на каждом языке
MAIN_BUTTONS = {
    "ru": {
        "expense": "Расход", "income": "Приход", "rezka": "Резка", "palirovka": "Палировка",
        "syre": "Сырье", "svet": "Свет", "nakoplenie": "Накопление",
        "help": "Помощь", "language": "🌐 Язык",
    },
    "uz": {
        "expense": "Xarajat", "income": "Kirim", "rezka": "Kesish", "palirovka": "Jilvirlash",
        "syre": "Xomashyo", "svet": "Svet", "nakoplenie": "Jamg'arma",
        "help": "Yordam", "language": "🌐 Til",
    },
}

MAIN_LAYOUT = [
    ["expense", "income"],
    ["rezka", "palirovka"],
    ["syre", "svet"],
    ["nakoplenie"],
    ["help"],
]

# подпись (в любом регистре/языке) -> action-код, для распознавания нажатой кнопки
ACTION_BY_LABEL = {}
for _lang, _buttons in MAIN_BUTTONS.items():
    for _action, _label in _buttons.items():
        ACTION_BY_LABEL[_label.strip().lower()] = _action
# устаревшее название "Катта" для Резки — оставлено для совместимости
ACTION_BY_LABEL["катта"] = "rezka"


def main_keyboard(lang: str) -> dict:
    buttons = MAIN_BUTTONS.get(lang, MAIN_BUTTONS[DEFAULT_LANG])
    rows = [[buttons[a] for a in row] for row in MAIN_LAYOUT]
    rows.append([buttons["language"]])
    return {"keyboard": rows, "resize_keyboard": True}


def language_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": LANG_LABELS["ru"], "callback_data": "lang:ru"}],
            [{"text": LANG_LABELS["uz"], "callback_data": "lang:uz"}],
        ]
    }


def contact_keyboard(lang: str) -> dict:
    label = {"ru": "📱 Отправить номер", "uz": "📱 Raqamni yuborish"}.get(lang, "📱 Отправить номер")
    return {
        "keyboard": [[{"text": label, "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


ASK_NAME_LABEL = {"ru": "Регистрация — Имя:", "uz": "Ro'yxatdan o'tish — Ism:"}

# label -> (prompt_type, lang), для распознавания на какое сообщение отвечает пользователь
PROMPT_LABELS = {
    "category": {"ru": "Категория:", "uz": "Kategoriya:"},
    "rezka": {"ru": "Резка — ФИО:", "uz": "Kesish — F.I.Sh:"},
    "palirovka": {"ru": "Палировка — ФИО:", "uz": "Jilvirlash — F.I.Sh:"},
    "nakoplenie": {"ru": "Накопление:", "uz": "Jamg'arma:"},
    "name": ASK_NAME_LABEL,
}


def match_prompt(reply_to_text: str):
    """Возвращает (prompt_type, label, lang) для reply_to_text, либо (None, None, None)."""
    for prompt_type, by_lang in PROMPT_LABELS.items():
        for lang, label in by_lang.items():
            if reply_to_text.startswith(label):
                return prompt_type, label, lang
    return None, None, None

_TEXT = {
    "ask_language": {
        "ru": "Привет! Для начала выбери язык:",
        "uz": "Salom! Avval tilni tanlang:",
    },
    "ask_contact": {
        "ru": "Отлично! Теперь поделись номером телефона — нажми кнопку ниже.",
        "uz": "Ajoyib! Endi telefon raqamingizni yuboring — pastdagi tugmani bosing.",
    },
    "ask_contact_reminder": {
        "ru": "Нажми на кнопку ниже и поделись номером — так и продолжим.",
        "uz": "Pastdagi tugmani bosib raqamingizni yuboring — shunda davom etamiz.",
    },
    "ask_name_prompt": {
        "ru": "Напиши своё Имя и Фамилию.\nНапример: Нодир Каримов",
        "uz": "Ismingiz va familiyangizni yozing.\nMasalan: Nodir Karimov",
    },
    "registered_done": {
        "ru": "Готово, {name}! Теперь можешь пользоваться ботом.",
        "uz": "Tayyor, {name}! Endi botdan foydalanishingiz mumkin.",
    },
    "language_changed": {
        "ru": "Язык переключён на русский.",
        "uz": "Til o'zbekchaga o'zgartirildi.",
    },
    "welcome": {
        "ru": (
            "Привет! Я записываю расходы/приходы завода в Google Таблицу.\n\n"
            "Быстрый способ:\n"
            "• Просто отправь число, например 50000 — запишется как расход\n"
            "• Отправь число со знаком +, например +50000 — запишется как приход\n\n"
            "Или нажми кнопку внизу, чтобы получить точный формат для нужной записи."
        ),
        "uz": (
            "Salom! Men zavodning xarajat/kirimlarini Google Jadvalga yozib boraman.\n\n"
            "Tezkor usul:\n"
            "• Shunchaki raqam yubor, masalan 50000 — xarajat sifatida yoziladi\n"
            "• + belgisi bilan yubor, masalan +50000 — kirim sifatida yoziladi\n\n"
            "Yoki pastdagi tugmani bos — kerakli yozuv uchun aniq formatni olasan."
        ),
    },
    "category_choose": {"ru": "Выбери категорию:", "uz": "Kategoriyani tanlang:"},
    "rezka_choose": {"ru": "Выбери, кто делал резку:", "uz": "Kesishni kim bajarganini tanlang:"},
    "palirovka_choose": {"ru": "Выбери, кто делал палировку:", "uz": "Jilvirlashni kim bajarganini tanlang:"},
    "category_prompt": {
        "ru": "Категория: {category}\nТеперь ответь на это сообщение суммой (и через запятую — наименованием).\nНапример: 50000, ужин с семьёй",
        "uz": "Kategoriya: {category}\nEndi shu xabarga summa bilan javob ber (vergul orqali — nomi).\nMasalan: 50000, oilaviy kechki ovqat",
    },
    "rezka_prompt": {
        "ru": "Резка — ФИО: {fio}\nТеперь ответь на это сообщение датой и м2 через запятую (дату можно пропустить — будет сегодня).\nНапример: 09.07.2026, 150  или просто  150",
        "uz": "Kesish — F.I.Sh: {fio}\nEndi shu xabarga sana va m2 ni vergul bilan yoz (sanani tashlab ketish mumkin — bugungi kun qo'yiladi).\nMasalan: 09.07.2026, 150  yoki shunchaki  150",
    },
    "rezka_prompt_other": {
        "ru": "Резка — ФИО: Другое\nНапиши ответом ФИО, дату и м2 через запятую.\nНапример: Расим, 09.07.2026, 150",
        "uz": "Kesish — F.I.Sh: Boshqa\nJavobida F.I.Sh, sana va m2 ni vergul bilan yoz.\nMasalan: Rasim, 09.07.2026, 150",
    },
    "palirovka_prompt": {
        "ru": "Палировка — ФИО: {fio}\nТеперь ответь на это сообщение датой и м2 через запятую (дату можно пропустить — будет сегодня).\nНапример: 09.07.2026, 400  или просто  400",
        "uz": "Jilvirlash — F.I.Sh: {fio}\nEndi shu xabarga sana va m2 ni vergul bilan yoz (sanani tashlab ketish mumkin — bugungi kun qo'yiladi).\nMasalan: 09.07.2026, 400  yoki shunchaki  400",
    },
    "palirovka_prompt_other": {
        "ru": "Палировка — ФИО: Другое\nНапиши ответом ФИО, дату и м2 через запятую.\nНапример: Расим, 09.07.2026, 400",
        "uz": "Jilvirlash — F.I.Sh: Boshqa\nJavobida F.I.Sh, sana va m2 ni vergul bilan yoz.\nMasalan: Rasim, 09.07.2026, 400",
    },
    "nakoplenie_prompt": {
        "ru": "Накопление:\nОтветь на это сообщение суммой и через запятую — комментарием.\nДата проставится сама (сегодняшняя).\nНапример: 500000, аванс за квартиру",
        "uz": "Jamg'arma:\nShu xabarga summa va vergul orqali — izoh bilan javob ber.\nSana o'zi qo'yiladi (bugungi).\nMasalan: 500000, kvartira uchun avans",
    },
    "help": {
        "ru": (
            "Не понял команду. Примеры:\n"
            "Расход: 50000, Категория: Ужин, Наименование: ужин\n"
            "Приход: 2000000, Наименование: аванс\n"
            "Резка, Дата: 09.07.2026, м2: 150, ФИО: Исмат\n"
            "Палировка, ФИО: Нодир, Дата: 09.07.2026, м2: 400\n"
            "Сырье, Описание: камень, Стоимость: 15000000, Дата: 09.07.2026, Кубы: 20\n"
            "Свет, Дата: 09.07.2026, Показание: 12600, Расход: 36, Тариф: 450\n"
            "Накопление: нажми кнопку и ответь суммой и комментарием через запятую\n\n"
            "Быстро: просто число — расход, число с + — приход."
        ),
        "uz": (
            "Buyruq tushunilmadi. Misollar:\n"
            "Расход: 50000, Категория: Ужин, Наименование: ужин\n"
            "Приход: 2000000, Наименование: аванс\n"
            "Резка, Дата: 09.07.2026, м2: 150, ФИО: Исмат\n"
            "Палировка, ФИО: Нодир, Дата: 09.07.2026, м2: 400\n"
            "Сырье, Описание: камень, Стоимость: 15000000, Дата: 09.07.2026, Кубы: 20\n"
            "Свет, Дата: 09.07.2026, Показание: 12600, Расход: 36, Тариф: 450\n"
            "Jamg'arma: tugmani bosing va summa bilan izohni vergul orqali yozing\n\n"
            "Tez: shunchaki raqam — xarajat, + bilan raqam — kirim.\n"
            "(Buyruqlar formati o'zgarmagan — rus tilida yoziladi, faqat bot menyusi tarjima qilingan.)"
        ),
    },
    "saved_expense": {"ru": "Расход записан (строка {row})", "uz": "Xarajat yozildi (qator {row})"},
    "saved_income": {"ru": "Приход записан (строка {row})", "uz": "Kirim yozildi (qator {row})"},
    "saved_rezka": {"ru": "Резка записана (строка {row})", "uz": "Kesish yozildi (qator {row})"},
    "saved_palirovka": {"ru": "Палировка записана (строка {row})", "uz": "Jilvirlash yozildi (qator {row})"},
    "saved_syre": {"ru": "Приход сырья записан (строка {row})", "uz": "Xomashyo kirimi yozildi (qator {row})"},
    "saved_svet": {"ru": "Расход света записан (строка {row})", "uz": "Svet xarajati yozildi (qator {row})"},
    "saved_nakoplenie": {"ru": "Накопление записано (строка {row})", "uz": "Jamg'arma yozildi (qator {row})"},
    "write_error": {
        "ru": "Ошибка при записи в таблицу: {error}",
        "uz": "Jadvalga yozishda xatolik: {error}",
    },
    "worker_entry_hint": {
        "ru": "Нужно ФИО и м2 через запятую, например: Расим, 150",
        "uz": "F.I.Sh va m2 kerak, vergul bilan, masalan: Rasim, 150",
    },
}

TYPE_TEMPLATES = {
    "расход": {
        "ru": (
            "Формат:\n"
            "Расход: <сумма>, Категория: <категория>, Наименование: <название>\n\n"
            "Например:\n"
            "Расход: 50000, Категория: Ужин, Наименование: ужин с семьёй\n\n"
            "Или быстро — просто отправь число: 50000"
        ),
        "uz": (
            "Format:\n"
            "Расход: <summa>, Категория: <kategoriya>, Наименование: <nomi>\n\n"
            "Masalan:\n"
            "Расход: 50000, Категория: Ужин, Наименование: oilaviy kechki ovqat\n\n"
            "Yoki tezroq — shunchaki raqam yuboring: 50000"
        ),
    },
    "приход": {
        "ru": (
            "Формат:\n"
            "Приход: <сумма>, Наименование: <название>\n\n"
            "Например:\n"
            "Приход: 2000000, Наименование: аванс от Жамшида\n\n"
            "Или быстро — отправь число со знаком плюс: +2000000"
        ),
        "uz": (
            "Format:\n"
            "Приход: <summa>, Наименование: <nomi>\n\n"
            "Masalan:\n"
            "Приход: 2000000, Наименование: Jamshiddan avans\n\n"
            "Yoki tezroq — plyus belgisi bilan raqam yuboring: +2000000"
        ),
    },
    "резка": {
        "ru": "Формат:\nРезка, Дата: <дата>, м2: <число>, ФИО: <имя>\n\nНапример:\nРезка, Дата: 09.07.2026, м2: 150, ФИО: Исмат",
        "uz": "Format:\nРезка, Дата: <sana>, м2: <son>, ФИО: <ism>\n\nMasalan:\nРезка, Дата: 09.07.2026, м2: 150, ФИО: Исмат",
    },
    "палировка": {
        "ru": "Формат:\nПалировка, ФИО: <имя>, Дата: <дата>, м2: <число>\n\nНапример:\nПалировка, ФИО: Нодир, Дата: 09.07.2026, м2: 400",
        "uz": "Format:\nПалировка, ФИО: <ism>, Дата: <sana>, м2: <son>\n\nMasalan:\nПалировка, ФИО: Нодир, Дата: 09.07.2026, м2: 400",
    },
    "сырье": {
        "ru": "Формат:\nСырье, Описание: <текст>, Стоимость: <сумма>, Дата: <дата>, Кубы: <число>\n\nНапример:\nСырье, Описание: партия камня, Стоимость: 15000000, Дата: 09.07.2026, Кубы: 20",
        "uz": "Format:\nСырье, Описание: <matn>, Стоимость: <summa>, Дата: <sana>, Кубы: <son>\n\nMasalan:\nСырье, Описание: tosh partiyasi, Стоимость: 15000000, Дата: 09.07.2026, Кубы: 20",
    },
    "свет": {
        "ru": "Формат:\nСвет, Дата: <дата>, Показание: <число>, Расход: <число>, Тариф: <число>\n\nНапример:\nСвет, Дата: 09.07.2026, Показание: 12600, Расход: 36, Тариф: 450",
        "uz": "Format:\nСвет, Дата: <sana>, Показание: <son>, Расход: <son>, Тариф: <son>\n\nMasalan:\nСвет, Дата: 09.07.2026, Показание: 12600, Расход: 36, Тариф: 450",
    },
    "накопление": {
        "ru": "Формат:\nСумма, Комментарий\n\nНапример:\n500000, аванс за квартиру\n\nДата проставится сама.",
        "uz": "Format:\nSumma, Izoh\n\nMasalan:\n500000, kvartira uchun avans\n\nSana o'zi qo'yiladi.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    entry = _TEXT.get(key, {})
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or ""
    return text.format(**kwargs) if kwargs else text


def type_template(action: str, lang: str) -> str:
    entry = TYPE_TEMPLATES.get(action, {})
    return entry.get(lang) or entry.get(DEFAULT_LANG) or t("help", lang)
