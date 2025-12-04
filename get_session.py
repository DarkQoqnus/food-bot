import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

OWNER_ID = int(os.environ["ADMIN_ID"])

API_ID_STEP, API_HASH_STEP, PHONE_STEP, CODE_STEP, PASSWORD_STEP = range(5)

def session_start(update: Update, ctx: CallbackContext) -> int:
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("❌ شما دسترسی ندارید.")
        return ConversationHandler.END
    update.message.reply_text("سلام! لطفاً API_ID خود را وارد کنید:")
    return API_ID_STEP

def get_api_id(update: Update, ctx: CallbackContext) -> int:
    text = update.message.text.strip()
    if not text.isdigit():
        update.message.reply_text("❌ لطفاً فقط عدد معتبر وارد کنید برای API_ID:")
        return API_ID_STEP
    ctx.user_data["api_id"] = int(text)
    update.message.reply_text("حالا API_HASH خود را وارد کنید:")
    return API_HASH_STEP

def get_api_hash(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["api_hash"] = update.message.text.strip()
    update.message.reply_text("شماره تلفن خود را وارد کنید (مثل +989xxxxxxxxx):")
    return PHONE_STEP

def get_phone(update: Update, ctx: CallbackContext) -> int:
    phone = update.message.text.strip()
    if not phone.startswith("+") or not phone[1:].isdigit():
        update.message.reply_text("❌ فرمت شماره نامعتبره. به شکل +989xxxxxxxxx وارد کن.")
        return PHONE_STEP

    ctx.user_data["phone"] = phone
    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]

    try:
        client = TelegramClient(StringSession(), api_id, api_hash)
        client.connect()
        ctx.user_data["client"] = client

        # درخواست کد همین‌جا
        client.send_code_request(phone)

        update.message.reply_text("کدی که تلگرام فرستاد را وارد کنید:")
        return CODE_STEP
    except Exception as e:
        update.message.reply_text(f"❌ خطا در ارسال کد: {e}")
        return ConversationHandler.END

def get_code(update: Update, ctx: CallbackContext) -> int:
    ctx.user_data["code"] = update.message.text.strip()
    update.message.reply_text("اگر رمز دو مرحله‌ای دارید وارد کنید، در غیر این صورت فقط بزنید -")
    return PASSWORD_STEP

def get_password(update: Update, ctx: CallbackContext) -> int:
    password = update.message.text.strip()
    if password == "-":
        password = None

    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]
    phone = ctx.user_data["phone"]
    code = ctx.user_data["code"]
    client = ctx.user_data.get("client")

    try:
        if client is None:
            client = TelegramClient(StringSession(), api_id, api_hash)
            client.connect()

        client.sign_in(phone=phone, code=code, password=password)
        session_string = client.session.save()
        update.message.reply_text(f"✅ Session String شما:\n\n{session_string}")
    except Exception as e:
        update.message.reply_text(f"❌ خطا در ورود: {e}")
    finally:
        try:
            if client:
                client.disconnect()
        except:
            pass
        ctx.user_data.clear()

    return ConversationHandler.END

def cancel(update: Update, ctx: CallbackContext) -> int:
    client = ctx.user_data.get("client")
    try:
        if client:
            client.disconnect()
    except:
        pass
    ctx.user_data.clear()
    update.message.reply_text("فرایند لغو شد.")
    return ConversationHandler.END

def get_conv_handler() -> ConversationHandler:
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
