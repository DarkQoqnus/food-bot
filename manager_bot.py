# manager_bot.py
from telegram.ext import Updater, CommandHandler
import config

active = True
filter_words = config.FILTER_WORDS
updater = Updater(config.BOT_TOKEN, use_context=True)

def start(update, context):
    update.message.reply_text("مدیریت ربات فعال شد ✅")

def toggle(update, context):
    global active
    active = not active
    status = "روشن" if active else "خاموش"
    update.message.reply_text(f"ربات الان {status} است")

def set_filter(update, context):
    global filter_words
    if context.args:
        filter_words = context.args
        update.message.reply_text(f"فیلتر تغییر کرد به: {filter_words}")
    else:
        update.message.reply_text("لطفاً کلمه جدید رو وارد کنید")

def report_to_manager(text):
    updater.bot.send_message(chat_id=config.GROUP_ID, text=text)

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("toggle", toggle))
updater.dispatcher.add_handler(CommandHandler("setfilter", set_filter))

def run_manager():
    updater.start_polling()
    updater.idle()
