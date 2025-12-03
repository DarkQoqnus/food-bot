import os
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# وضعیت مشترک با main.py
active = True
filter_words = [
    "سلف", "سلف فروشی", "سلف میفروشم",
    "حافظ", "حافظ فروشی", "حافظ میفروشم"
]

updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

def is_admin(update):
    user_id = update.effective_user.id
    return user_id == ADMIN_ID

def start(update, context):
    if not is_admin(update):
        return
    update.message.reply_text("مدیریت ربات فعال شد ✅")

def toggle(update, context):
    global active
    if not is_admin(update):
        return
    active = not active
    status = "روشن" if active else "خاموش"
    update.message.reply_text(f"شنود پیام‌ها الان {status} است")

def setfilter(update, context):
    global filter_words
    if not is_admin(update):
        return
    if context.args:
        # مثال: /setfilter سلف حافظ
        filter_words = context.args
        update.message.reply_text(f"فیلترها تنظیم شد: {', '.join(filter_words)}")
    else:
        update.message.reply_text("لطفاً یک یا چند کلمه بده: /setfilter سلف حافظ")

def report_to_manager(text):
    # گزارش فقط به مدیر ارسال می‌شود
    updater.bot.send_message(chat_id=ADMIN_ID, text=text)

def start_manager():
    # Polling را بدون بلاک کردن شروع می‌کند
    updater.start_polling()

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("toggle", toggle))
dp.add_handler(CommandHandler("setfilter", setfilter))
