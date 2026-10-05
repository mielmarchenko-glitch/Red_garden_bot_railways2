import os
from dotenv import load_dotenv

# Загружаем переменные из локального файла .env (если он есть)
load_dotenv()

# Получаем секретные ключи из окружения (на Railway они будут взяты из Variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Контакты старшего продавца и локация магазина «Красный сад» в Ташкенте
SENIOR_SALES_CONTACT = "Нодира: +998 93 788 78 33"

SHOP_LOCATION = {
    "latitude": 41.279446,
    "longitude": 69.178788,
    "address": "Магазин «Красный сад» (Ташкент)"
}

# ID Telegram-группы «Красный кандидаты» для HR-уведомлений
HR_GROUP_CHAT_ID = -1003775981406