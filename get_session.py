import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler

# فقط برای مدیر اصلی
OWNER_ID = int(os.environ["ADMIN_ID"])

# مراحل گفتگو
API_ID_STEP, API_HASH_STEP, PHONE_STEP, CODE_STEP, PASSWORD_STEP = range(5)

def session_start(update, ctx):
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("❌ شما دسترسی ندارید.")
        return ConversationHandler.END
    update.message.reply_text("سلام! لطفاً API_ID خود را وارد کنید:")
    return API_ID_STEP

def get_api_id(update, ctx):
    ctx.user_data["api_id"] = int(update.message.text.strip())
    update.message.reply_text("حالا API_HASH خود را وارد کنید:")
    return API_HASH_STEP

def get_api_hash(update, ctx):
    ctx.user_data["api_hash"] = update.message.text.strip()
    update.message.reply_text("شماره تلفن خود را وارد کنید (با کد کشور):")
    return PHONE_STEP

def get_phone(update, ctx):
    ctx.user_data["phone"] = update.message.text.strip()
    update.message.reply_text("کدی که تلگرام فرستاد را وارد کنید:")
    return CODE_STEP

def get_code(update, ctx):
    ctx.user_data["code"] = update.message.text.strip()
    update.message.reply_text("اگر رمز دو مرحله‌ای دارید وارد کنید، در غیر این صورت فقط بزنید -")
    return PASSWORD_STEP

def get_password(update, ctx):
    password = update.message.text.strip()
    if password == "-":
        password = None
    ctx.user_data["password"] = password

    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]
    phone = ctx.user_data["phone"]
    code = ctx.user_data["code"]

    try:
        client = TelegramClient(StringSession(), api_id, api_hash)
        client.connect()
        if not client.is_user_authorized():
            client.sign_in(phone=phone, code=code, password=password)
        session_string = client.session.save()
        update.message.reply_text(f"✅ Session String شما:\n\n{session_string}")
        client.disconnect()
    except Exception as e:
        update.message.reply_text(f"❌ خطا: {e}")

    return ConversationHandler.END

def cancel(update, ctx):
    update.message.reply_text("فرایند لغو شد.")
    return ConversationHandler.END

def get_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("session", session_start)],
        states={
            API_ID_STEP: [MessageHandler(Filters.text & ~Filters.command, get_api_id)],
            API_HASH_STEP: [MessageHandler(Filters.text & ~Filters.command, get_api_hash)],
            PHONE_STEP: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            CODE_STEP: [MessageHandler(Filters.text & ~Filters.command, get_code)],
            PASSWORD_STEP: [MessageHandler(Filters.text & ~Filters.command, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
