import os
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # فقط مدیر

active = True
filter_words = [
    "سلف", "سلف فروشی", "سلف میفروشم",
    "حافظ", "حافظ فروشی", "حافظ میفروشم"
]

updater = Updater(BOT_TOKEN, use_context=True)

def check_admin(update):
    """بررسی می‌کنه فقط مدیر بتونه دستور بده"""
    user_id = update.effective_user.id
    return user_id == ADMIN_ID

def start(update, context):
    if not check_admin(update):
        return
    update.message.reply_text("مدیریت ربات فعال شد ✅")

def toggle(update, context):
    global active
    if not check_admin(update):
        return
    active = not active
    status = "روشن" if active else "خاموش"
    update.message.reply_text(f"ربات الان {status} است")

def set_filter(update, context):
    global filter_words
    if not check_admin(update):
        return
    if context.args:
        filter_words = context.args
        update.message.reply_text(f"فیلتر تغییر کرد به: {filter_words}")
    else:
        update.message.reply_text("لطفاً کلمه جدید رو وارد کنید")

def report_to_manager(text):
    updater.bot.send_message(chat_id=ADMIN_ID, text=text)

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("toggle", toggle))
updater.dispatcher.add_handler(CommandHandler("setfilter", set_filter))

def run_manager():
    updater.start_polling()
    updater.idle()
