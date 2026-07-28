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
        "expense": "Расход", "income": "Приход", "rezka": "Обьем ребят за день",
        "syre": "Сырье", "svet": "Свет", "nakoplenie": "Накопление",
        "report": "Отчёт", "abdulkosim": "Абулкосим", "help": "Помощь", "language": "🌐 Язык",
    },
    "uz": {
        "expense": "Xarajat", "income": "Kirim", "rezka": "Kunlik kesilgan Obyem",
        "syre": "Xomashyo", "svet": "Svet", "nakoplenie": "Jamg'arma",
        "report": "Hisobot", "abdulkosim": "Абулкосим", "help": "Yordam", "language": "🌐 Til",
    },
}

MAIN_LAYOUT = [
    ["expense", "income"],
    ["rezka"],
    ["syre", "svet"],
    ["nakoplenie", "report"],
    ["abdulkosim"],
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
    "rezka": {"ru": "Обьем — ФИО:", "uz": "Obyem — F.I.Sh:"},
    "nakoplenie": {"ru": "Накопление:", "uz": "Jamg'arma:"},
    "abdulkosim": {"ru": "Абулкосим:", "uz": "Абулкосим:"},
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
    "rezka_choose": {"ru": "Выбери, за кого записать объём:", "uz": "Kimning obyemini yozamiz — tanlang:"},
    "report_choose": {"ru": "Какой отчёт нужен?", "uz": "Qaysi hisobot kerak?"},
    "report_category": {
        "ru": "Расход «{category}» за всё время: {sum}",
        "uz": "«{category}» bo'yicha xarajat: {sum}",
    },
    "report_income": {"ru": "Общий приход за всё время: {sum}", "uz": "Umumiy kirim: {sum}"},
    "report_syre": {"ru": "Приход сырья за всё время: {sum}", "uz": "Umumiy xomashyo kirimi: {sum}"},
    "category_prompt": {
        "ru": "Категория: {category}\nТеперь ответь на это сообщение суммой (и через запятую — наименованием).\nНапример: 50000, ужин с семьёй",
        "uz": "Kategoriya: {category}\nEndi shu xabarga summa bilan javob ber (vergul orqali — nomi).\nMasalan: 50000, oilaviy kechki ovqat",
    },
    "rezka_prompt": {
        "ru": "Обьем — ФИО: {fio}\nТеперь ответь на это сообщение датой и м2 через запятую (дату можно пропустить — будет сегодня).\nНапример: 09.07.2026, 150  или просто  150",
        "uz": "Obyem — F.I.Sh: {fio}\nEndi shu xabarga sana va m2 ni vergul bilan yoz (sanani tashlab ketish mumkin — bugungi kun qo'yiladi).\nMasalan: 09.07.2026, 150  yoki shunchaki  150",
    },
    "rezka_prompt_other": {
        "ru": "Обьем — ФИО: Другое\nНапиши ответом ФИО, дату и м2 через запятую.\nНапример: Расим, 09.07.2026, 150",
        "uz": "Obyem — F.I.Sh: Boshqa\nJavobida F.I.Sh, sana va m2 ni vergul bilan yoz.\nMasalan: Rasim, 09.07.2026, 150",
    },
    "nakoplenie_prompt": {
        "ru": "Накопление:\nОтветь на это сообщение суммой и через запятую — комментарием.\nДата проставится сама (сегодняшняя).\nНапример: 500000, аванс за квартиру",
        "uz": "Jamg'arma:\nShu xabarga summa va vergul orqali — izoh bilan javob ber.\nSana o'zi qo'yiladi (bugungi).\nMasalan: 500000, kvartira uchun avans",
    },
    "abdulkosim_prompt": {
        "ru": "Абулкосим:\nОтветь на это сообщение наименованием и суммой через запятую (дату можно пропустить — будет сегодня).\nНапример: аванс, 500000  или  аванс, 500000, 09.07.2026",
        "uz": "Абулкосим:\nShu xabarga nomi va summani vergul bilan yoz (sanani tashlab ketish mumkin — bugungi kun qo'yiladi).\nMasalan: аванс, 500000  yoki  аванс, 500000, 09.07.2026",
    },
    "help": {
        "ru": (
            "Не понял команду. Примеры:\n"
            "Расход: 50000, Категория: Ужин, Наименование: ужин\n"
            "Приход: 2000000, Наименование: аванс\n"
            "Резка, Дата: 09.07.2026, м2: 150, ФИО: Исмат\n"
            "Сырье, партия камня, 15000000, 09.07.2026, 20\n"
            "Свет, 12600, 36\n"
            "Накопление: нажми кнопку и ответь суммой и комментарием через запятую\n\n"
            "Быстро: просто число — расход, число с + — приход."
        ),
        "uz": (
            "Buyruq tushunilmadi. Misollar:\n"
            "Расход: 50000, Категория: Ужин, Наименование: ужин\n"
            "Приход: 2000000, Наименование: аванс\n"
            "Резка, Дата: 09.07.2026, м2: 150, ФИО: Исмат\n"
            "Сырье, партия камня, 15000000, 09.07.2026, 20\n"
            "Свет, 12600, 36\n"
            "Jamg'arma: tugmani bosing va summa bilan izohni vergul orqali yozing\n\n"
            "Tez: shunchaki raqam — xarajat, + bilan raqam — kirim.\n"
            "(Buyruqlar formati o'zgarmagan — rus tilida yoziladi, faqat bot menyusi tarjima qilingan.)"
        ),
    },
    "saved_expense": {"ru": "Расход записан (строка {row})", "uz": "Xarajat yozildi (qator {row})"},
    "saved_income": {"ru": "Приход записан (строка {row})", "uz": "Kirim yozildi (qator {row})"},
    "saved_rezka": {"ru": "Объём записан (строка {row})", "uz": "Obyem yozildi (qator {row})"},
    "saved_syre": {"ru": "Приход сырья записан (строка {row})", "uz": "Xomashyo kirimi yozildi (qator {row})"},
    "saved_svet": {"ru": "Расход света записан (строка {row})", "uz": "Svet xarajati yozildi (qator {row})"},
    "saved_nakoplenie": {"ru": "Накопление записано (строка {row})", "uz": "Jamg'arma yozildi (qator {row})"},
    "saved_abdulkosim": {"ru": "Приход Абулкосима записан (строка {row})", "uz": "Abulqosim kirimi yozildi (qator {row})"},
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
    "сырье": {
        "ru": (
            "Формат (без подписей, по порядку через запятую):\n"
            "Сырье, <Описание>, <Стоимость>, <Дата>, <Кубы>\n\n"
            "Например:\n"
            "Сырье, партия камня, 15000000, 09.07.2026, 20\n\n"
            "Дату можно оставить пустой (просто запятая подряд) — подставится сегодняшняя."
        ),
        "uz": (
            "Format (yozuvlarsiz, vergul bilan ketma-ket):\n"
            "Сырье, <Tavsif>, <Narx>, <Sana>, <Kub>\n\n"
            "Masalan:\n"
            "Сырье, tosh partiyasi, 15000000, 09.07.2026, 20\n\n"
            "Sanani bo'sh qoldirish mumkin (ketma-ket vergul) — bugungi kun qo'yiladi."
        ),
    },
    "свет": {
        "ru": (
            "Формат (без подписей, по порядку через запятую):\n"
            "Свет, <Показание>, <Расход>\n\n"
            "Например:\n"
            "Свет, 12600, 36\n\n"
            "Тариф фиксированный (1100 сум), дата ставится сегодняшняя автоматически."
        ),
        "uz": (
            "Format (yozuvlarsiz, vergul bilan ketma-ket):\n"
            "Свет, <Ko'rsatkich>, <Sarf>\n\n"
            "Masalan:\n"
            "Свет, 12600, 36\n\n"
            "Tarif doimiy (1100 so'm), sana avtomatik bugungi kun qo'yiladi."
        ),
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
