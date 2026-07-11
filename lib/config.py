import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
CRON_SECRET = os.environ.get("CRON_SECRET", "")

WS_EXPENSES = "Личные Расходы"
WS_SALARY = "Болларни Ойлиги Обьем"
WS_BUSINESS = "Бизнес"
