# handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ai_interview import generate_ai_response
from database import save_candidate, check_candidate_exists, ADMIN_TELEGRAM_ID
from config import SENIOR_SALES_CONTACT, SHOP_LOCATION, HR_GROUP_CHAT_ID

router = Router()

class InterviewState(StatesGroup):
    choosing_language = State()
    chatting_with_ai = State()

chat_histories = {}
user_languages = {}

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    chat_histories[user_id] = []
    
    if check_candidate_exists(user_id):
        await message.answer(
            "⚠️ Вы уже проходили собеседование в нашу компанию ранее.\n"
            "Ваша анкета уже зарегистрирована в системе. Ожидайте обратной связи от отдела персонала.",
            parse_mode=None
        )
        return

    if user_id == ADMIN_TELEGRAM_ID:
        await message.answer("👑 *Режим тестировщика:* Ограничения на повторное прохождение сняты.", parse_mode="Markdown")

    # Первый шаг: Выбор языка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_uz")
        ]
    ])
    
    await message.answer(
        f"Здравствуйте, {message.from_user.full_name}!\n"
        "Добро пожаловать в службу персонала сети магазинов «Красный сад» в Ташкенте.\n\n"
        "Пожалуйста, выберите язык для прохождения собеседования:\n"
        "Iltimos, suhbat uchun tilni tanlang:",
        reply_markup=keyboard,
        parse_mode=None
    )
    await state.set_state(InterviewState.choosing_language)

@router.callback_query(F.data.startswith("lang_"))
async def process_language_choice(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = "ru" if callback.data == "lang_ru" else "uz"
    user_languages[user_id] = lang
    
    await state.update_data(lang=lang, shift_name="Продавец ночной смены (Учтепинский район)")
    
    intro_text = (
        "🌙 В настоящее время в сети «Красный сад» открыта вакансия:\n"
        "**Продавец ночной смены в Учтепинском районе**.\n\n"
        "Давайте проведем короткое предварительное собеседование!"
        if lang == "ru" else
        "🌙 Hozirgi vaqtda «Krasniy sad» tarmog'ida bo'sh ish o'rni mavjud:\n"
        "**Uchtepa tumanidagi tungi smena sotuvchisi**.\n\n"
        "Keling, qisqacha dastlabki suhbatdan o'tamiz!"
    )
    
    await callback.message.answer(intro_text, parse_mode=None)
    
    # Запускаем первый вопрос от ИИ
    initial_ai_msg = generate_ai_response([], lang)
    chat_histories[user_id].append({"role": "assistant", "content": initial_ai_msg})
    
    await callback.message.answer(initial_ai_msg, parse_mode=None)
    await state.set_state(InterviewState.chatting_with_ai)
    await callback.answer()

@router.message(InterviewState.chatting_with_ai)
async def process_ai_dialogue(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text
    bot_instance = message.bot
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    shift_name = "Продавец ночной смены (Учтепинский район)"
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    chat_histories[user_id].append({"role": "user", "content": user_text})
    
    ai_response = generate_ai_response(chat_histories[user_id], lang)
    chat_histories[user_id].append({"role": "assistant", "content": ai_response})
    
    username_str = f"@{message.from_user.username}" if message.from_user.username else "нет username"
    candidate_full_name = message.from_user.full_name
    
    if "[VERDICT: PASS]" in ai_response:
        clean_response = ai_response.replace("[VERDICT: PASS]", "").strip()
        if clean_response:
            await message.answer(clean_response, parse_mode=None)
        
        save_candidate(
            telegram_id=user_id,
            full_name=candidate_full_name,
            username=message.from_user.username or "нет",
            shift_type=shift_name,
            status="PASS"
        )
        
        success_msg = (
            "🎉 Поздравляем! Вы успешно прошли предварительный отбор.\n\n"
            "Приглашаем вас прийти в магазин для знакомства и прохождения дальнейшей стажировки.\n\n"
            f"📞 Свяжитесь со старшим продавцом ({SENIOR_SALES_CONTACT})\n"
            f"📍 Адрес магазина: {SHOP_LOCATION['address']}"
            if lang == "ru" else
            "🎉 Tabriklaymiz! Siz dastlabki suhbatdan muvaffaqiyatli o'tdingiz.\n\n"
            "Sizni do'kon bilan tanishish va amaliyot o'tash uchun taklif qilamiz.\n\n"
            f"📞 Katta sotuvchi bilan bog'laning ({SENIOR_SALES_CONTACT})\n"
            f"📍 Manzil: {SHOP_LOCATION['address']}"
        )
        
        await message.answer(success_msg, parse_mode=None)
        await message.answer_location(
            latitude=SHOP_LOCATION["latitude"],
            longitude=SHOP_LOCATION["longitude"]
        )
        
        if HR_GROUP_CHAT_ID:
            try:
                hr_notification = (
                    f"✅ **Новый успешный кандидат!**\n\n"
                    f"👤 Имя: {candidate_full_name}\n"
                    f"🔗 Профиль: {username_str} (ID: `{user_id}`)\n"
                    f"🎯 Вакансия: {shift_name} ({lang.upper()})\n"
                    f"📌 Статус: Успешно прошел скрининг (PASS)"
                )
                await bot_instance.send_message(chat_id=HR_GROUP_CHAT_ID, text=hr_notification, parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки в HR-группу: {e}")
                
        await state.clear()
        
    elif "[VERDICT: FAIL]" in ai_response:
        clean_response = ai_response.replace("[VERDICT: FAIL]", "").strip()
        if clean_response:
            await message.answer(clean_response, parse_mode=None)
        
        save_candidate(
            telegram_id=user_id,
            full_name=candidate_full_name,
            username=message.from_user.username or "нет",
            shift_type=shift_name,
            status="FAIL"
        )
        
        fail_msg = (
            "Спасибо за уделенное время. К сожалению, в данный момент вы не подходите под наши критерии. Желаем успехов!"
            if lang == "ru" else
            "Vaqtingiz uchun rahmat. Afsuski, hozirgi paytda talablarimizga mos kelmaysiz. O'qish va ishingizga omad!"
        )
        await message.answer(fail_msg, parse_mode=None)
        
        if HR_GROUP_CHAT_ID:
            try:
                hr_notification = (
                    f"❌ **Кандидат отклонен скринингом**\n\n"
                    f"👤 Имя: {candidate_full_name}\n"
                    f"🔗 Профиль: {username_str} (ID: `{user_id}`)\n"
                    f"🎯 Вакансия: {shift_name} ({lang.upper()})\n"
                    f"📌 Статус: Отклонен (FAIL)"
                )
                await bot_instance.send_message(chat_id=HR_GROUP_CHAT_ID, text=hr_notification, parse_mode="Markdown")
            except Exception as e:
                print(f"Ошибка отправки в HR-группу: {e}")
                
        await state.clear()
    else:
        await message.answer(ai_response, parse_mode=None)