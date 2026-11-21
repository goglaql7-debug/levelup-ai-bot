"""Levelup Mathh AI Telegram bot: text + photo mathematics tutor.

Python 3.10+. Run: python bot.py
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from typing import Any

from core import (
    MAX_PHOTO_BYTES, MAX_QUESTION_LENGTH, HISTORY_MESSAGES, MODE_NAMES,
    allowed_to_ask, build_model_input, get_instructions, split_long_text,
)
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

LOG = logging.getLogger("levelup_ai_bot")
BOT_NAME = "Levelup Mathh AI"


def mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("SAT Math", callback_data="mode:sat")],
            [InlineKeyboardButton("Milliy sertifikat", callback_data="mode:milliy")],
            [InlineKeyboardButton("Umumiy matematika", callback_data="mode:general")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.setdefault("mode", "general")
    await update.effective_message.reply_text(
        "Levelup Mathh AI botiga xush kelibsiz!\n\n"
        "Men masalalarni qadamma-qadam tushuntiraman. "
        "Savolni yozing yoki misolning rasmini yuboring.\n\n"
        "Avval o'z yo'nalishingizni tanlang:",
        reply_markup=mode_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Buyruqlar:\n"
        "/start — boshlash va yo'nalish tanlash\n"
        "/sat — SAT Math rejimi\n"
        "/milliy — Milliy sertifikat rejimi\n"
        "/umumiy — umumiy matematika rejimi\n"
        "/kurslar — kurs yo'nalishlari haqida\n"
        "/reset — suhbat xotirasini tozalash\n"
        "/privacy — maxfiylik haqida\n"
        "/help — yordam\n\n"
        "Matn yoki matematika masalasi tasvirini yuboring. "
        "Foto ostiga savol yozishingiz ham mumkin."
    )


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    context.user_data["mode"] = mode
    context.user_data.pop("history", None)
    await update.effective_message.reply_text(
        f"Yo'nalish: {MODE_NAMES[mode]}.\n"
        "Savolingizni yozing yoki rasm yuboring."
    )


async def set_sat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_mode(update, context, "sat")


async def set_milliy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_mode(update, context, "milliy")


async def set_umumiy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_mode(update, context, "general")


async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    choice = query.data.split(":", 1)[-1] if query.data else ""
    if choice not in MODE_NAMES:
        return
    context.user_data["mode"] = choice
    context.user_data.pop("history", None)
    await query.edit_message_text(
        f"Yo'nalish tanlandi: {MODE_NAMES[choice]}.\n\n"
        "Endi masalangizni yozing yoki rasmini yuboring."
    )


async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Levelup Mathh yo'nalishlari:\n"
        "1. SAT Math — Digital SAT matematikasiga tayyorgarlik.\n"
        "2. Milliy sertifikat — matematika sertifikati uchun tayyorgarlik.\n\n"
        "Bu bot savollarga yordam berish uchun mo'ljallangan. "
        "Kurs narxlari va qabul jadvali bu namunaviy versiyaga kiritilmagan; "
        "ularni administrator tasdiqlagach qo'shish mumkin."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("history", None)
    await update.effective_message.reply_text(
        "Suhbat xotirasi tozalandi. Yangi savol yuborishingiz mumkin."
    )


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Maxfiylik:\n"
        "• Savol va yuborilgan rasm AI javobini olish uchun OpenAI APIga uzatiladi.\n"
        "• Bot suhbat tarixini ish jarayonidagi xotirada vaqtincha saqlaydi, "
        "doimiy ma'lumotlar bazasiga yozmaydi.\n"
        "• /reset shu suhbat tarixini bot xotirasidan o'chiradi.\n"
        "• Botni qayta ishga tushirganda vaqtinchalik tarix yo'qoladi.\n"
        "• Shaxsiy maxfiy ma'lumotlar va parollarni yubormang.\n"
        "• Uchinchi tomon servislarining ma'lumotlarni saqlash qoidalari alohida amal qiladi."
    )


async def send_answer(update: Update, answer: str) -> None:
    for chunk in split_long_text(answer):
        await update.effective_message.reply_text(chunk)


async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    text = (message.caption if message.photo else message.text) or ""
    text = text.strip()
    if len(text) > MAX_QUESTION_LENGTH:
        await message.reply_text(
            f"Savol juda uzun. Iltimos, {MAX_QUESTION_LENGTH} belgidan qisqaroq qilib yuboring."
        )
        return

    has_photo = bool(message.photo)
    if not text and not has_photo:
        return

    limit: int = context.application.bot_data["hourly_limit"]
    usage: deque[float] = context.user_data.setdefault("usage", deque())
    if not allowed_to_ask(usage, time.monotonic(), limit):
        await message.reply_text(
            "Bir soatlik savollar limiti tugadi. Keyinroq qayta urinib ko'ring."
        )
        return

    prompt = text or "Rasmdagi matematik masalani o'qing, tushuntiring va qadamma-qadam yeching."
    image_bytes: bytes | None = None
    if has_photo:
        largest = message.photo[-1]
        if largest.file_size and largest.file_size > MAX_PHOTO_BYTES:
            await message.reply_text("Rasm hajmi juda katta. Kichikroq fotosurat yuboring.")
            return
        try:
            tg_file = await largest.get_file()
            image_bytes = bytes(await tg_file.download_as_bytearray())
            if len(image_bytes) > MAX_PHOTO_BYTES:
                await message.reply_text("Rasm hajmi juda katta. Kichikroq fotosurat yuboring.")
                return
        except Exception:
            LOG.exception("Telegram rasm yuklashda xato")
            await message.reply_text("Rasmni yuklay olmadim. Qaytadan yuboring.")
            return

    history: list[dict[str, Any]] = context.user_data.setdefault("history", [])
    mode: str = context.user_data.get("mode", "general")
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)

    client: AsyncOpenAI = context.application.bot_data["client"]
    model: str = context.application.bot_data["model"]
    try:
        result = await client.responses.create(
            model=model,
            instructions=get_instructions(mode),
            input=build_model_input(history, prompt, image_bytes=image_bytes),
            max_output_tokens=1600,
            store=False,
        )
        answer = (result.output_text or "").strip()
        if not answer:
            await message.reply_text(
                "Javobni tayyorlab bo'lmadi. Savolingizni boshqacha yozib ko'ring."
            )
            return
    except AuthenticationError:
        LOG.warning("OpenAI autentifikatsiya xatosi")
        await message.reply_text("AI kaliti ishlamayapti. Bot administratoriga xabar bering.")
        return
    except RateLimitError:
        LOG.warning("OpenAI so'rov/kvota cheklovi")
        await message.reply_text("AI xizmatida limit yoki balans muammosi bor. Keyinroq urinib ko'ring.")
        return
    except (APIConnectionError, APITimeoutError, APIStatusError) as exc:
        LOG.warning("OpenAI vaqtinchalik xato: %s", type(exc).__name__)
        await message.reply_text("AI xizmati vaqtincha javob bermadi. Keyinroq urinib ko'ring.")
        return
    except Exception:
        LOG.exception("Kutilmagan AI xatosi")
        await message.reply_text("Texnik xato yuz berdi. Keyinroq qayta urinib ko'ring.")
        return

    # Images are not retained; only the text descriptor of the question remains in RAM.
    summary = prompt if image_bytes is None else "[Foydalanuvchi rasm yuborgan] " + prompt
    history.extend(
        [
            {"role": "user", "content": summary},
            {"role": "assistant", "content": answer[:10000]},
        ]
    )
    context.user_data["history"] = history[-HISTORY_MESSAGES:]
    await send_answer(update, answer)


async def unsupported_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Hozircha matn va fotosuratlarni tushuna olaman. "
        "Savolingizni yozing yoki rasm yuboring."
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOG.error("Telegram handler xatosi: %s", type(context.error).__name__)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Botni boshlash"),
            BotCommand("sat", "SAT Math rejimi"),
            BotCommand("milliy", "Milliy sertifikat rejimi"),
            BotCommand("umumiy", "Umumiy matematika"),
            BotCommand("kurslar", "Yo'nalishlar"),
            BotCommand("reset", "Suhbat xotirasini tozalash"),
            BotCommand("privacy", "Maxfiylik"),
            BotCommand("help", "Yordam"),
        ]
    )
    LOG.info("Bot ishga tushdi: @%s", (await application.bot.get_me()).username)


async def post_shutdown(application: Application) -> None:
    await application.bot_data["client"].close()


def build_application(token: str, api_key: str, model: str, hourly_limit: int) -> Application:
    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["client"] = AsyncOpenAI(api_key=api_key, timeout=45.0, max_retries=1)
    app.bot_data["model"] = model
    app.bot_data["hourly_limit"] = hourly_limit

    private = filters.ChatType.PRIVATE
    app.add_handler(CommandHandler("start", start, filters=private))
    app.add_handler(CommandHandler("help", help_command, filters=private))
    app.add_handler(CommandHandler("sat", set_sat, filters=private))
    app.add_handler(CommandHandler("milliy", set_milliy, filters=private))
    app.add_handler(CommandHandler("umumiy", set_umumiy, filters=private))
    app.add_handler(CommandHandler("kurslar", courses, filters=private))
    app.add_handler(CommandHandler("reset", reset, filters=private))
    app.add_handler(CommandHandler("privacy", privacy, filters=private))
    app.add_handler(CallbackQueryHandler(choose_mode, pattern=r"^mode:(sat|milliy|general)$"))
    app.add_handler(MessageHandler(private & (filters.TEXT & ~filters.COMMAND | filters.PHOTO), process_question))
    app.add_handler(MessageHandler(private & ~filters.COMMAND, unsupported_message))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Avoid verbose HTTP logs that may include request metadata.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    try:
        hourly_limit = max(1, int(os.getenv("QUESTIONS_PER_HOUR", "20")))
    except ValueError:
        raise SystemExit("QUESTIONS_PER_HOUR butun son bo'lishi kerak.")
    if not telegram_token or telegram_token == "BOTFATHER_TOKEN_SHU_YERGA":
        raise SystemExit("TELEGRAM_BOT_TOKEN to'ldirilmagan. .env faylini tekshiring.")
    if not api_key or api_key == "OPENAI_API_KEY_SHU_YERGA":
        raise SystemExit("OPENAI_API_KEY to'ldirilmagan. .env faylini tekshiring.")
    LOG.info("Levelup Mathh AI bot ishga tushmoqda. Model: %s", model)
    application = build_application(telegram_token, api_key, model, hourly_limit)
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
