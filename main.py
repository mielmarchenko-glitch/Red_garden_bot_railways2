# main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from handlers import router

# Ваш реальный токен Telegram-бота
TOKEN = "8915282460:AAHnjwAH2l5LOZV29bh8BUYr3D1Go4fMNpY"

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("Бот запущен и готов принимать кандидатов сети «Красный сад»!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())