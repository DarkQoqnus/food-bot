import os
from typing import Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# فقط برای مدیر اصلی
OWNER_ID = int(os.environ["ADMIN_ID"])

# مراحل گفتگو
API_ID_STEP, API_HASH_STEP, PHONE_STEP, CODE_STEP, PASSWORD_STEP = range(5)


async def session_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return ConversationHandler.END
    await update.message.reply_text("سلام! لطفاً API_ID خود را وارد کنید:")
    return API_ID_STEP


async def get_api_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ لطفاً فقط عدد معتبر وارد کنید برای API_ID:")
        return API_ID_STEP
    ctx.user_data["api_id"] = int(text)
    await update.message.reply_text("حالا API_HASH خود را وارد کنید:")
    return API_HASH_STEP


async def get_api_hash(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["api_hash"] = update.message.text.strip()
    await update.message.reply_text("شماره تلفن خود را وارد کنید (مثل +989xxxxxxxxx):")
    return PHONE_STEP


async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if not phone.startswith("+") or not phone[1:].isdigit():
        await update.message.reply_text("❌ فرمت شماره نامعتبره. به شکل +989xxxxxxxxx وارد کن.")
        return PHONE_STEP

    ctx.user_data["phone"] = phone

    # ساخت کلاینت و ارسال درخواست کد همین‌جا
    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]

    try:
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        ctx.user_data["client"] = client  # نگه‌داری برای مراحل بعدی

        # درخواست کد (تلگرام تصمیم می‌گیره داخل اپ یا SMS بفرسته)
        await client.send_code_request(phone)  # اگر لازم بود: force_sms=True

        await update.message.reply_text("کدی که تلگرام فرستاد را وارد کنید:")
        return CODE_STEP
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال کد: {e}")
        # تمیزکاری در صورت خطا
        try:
            client = ctx.user_data.get("client")
            if client:
                await client.disconnect()
        except:
            pass
        ctx.user_data.clear()
        return ConversationHandler.END


async def get_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["code"] = update.message.text.strip()
    await update.message.reply_text("اگر رمز دو مرحله‌ای دارید وارد کنید، در غیر این صورت فقط بزنید -")
    return PASSWORD_STEP


async def get_password(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    if password == "-":
        password = None
    ctx.user_data["password"] = password

    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]
    phone = ctx.user_data["phone"]
    code = ctx.user_data["code"]
    client: TelegramClient | None = ctx.user_data.get("client")

    try:
        if client is None:
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.connect()

        # ورود با کد و در صورت نیاز رمز دو مرحله‌ای
        await client.sign_in(phone=phone, code=code, password=password)

        session_string = client.session.save()
        await update.message.reply_text(f"✅ Session String شما:\n\n{session_string}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ورود: {e}")
    finally:
        try:
            if client:
                await client.disconnect()
        except:
            pass
        ctx.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    # قطع ارتباط اگر کلاینت ساخته شده
    try:
        client: TelegramClient | None = ctx.user_data.get("client")
        if client:
            await client.disconnect()
    except:
        pass
    ctx.user_data.clear()
    await update.message.reply_text("فرایند لغو شد.")
    return ConversationHandler.END


def get_conv_handler() -> ConversationHandler:
    # توجه: این نسخه برای python-telegram-bot v20+ است (filters به‌جای Filters و هندلرهای async)
    return ConversationHandler(
        entry_points=[CommandHandler("session", session_start)],
        states={
            API_ID_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_id),
            ],
            API_HASH_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_hash),
            ],
            PHONE_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            CODE_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_code),
            ],
            PASSWORD_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_password),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
