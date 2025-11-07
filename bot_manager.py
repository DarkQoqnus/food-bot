from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import os

BOT_TOKEN = os.environ['BOT_TOKEN']

async def start_command(update: Update, context: CallbackContext):
    print("دریافت دستور /panel از کاربر: ", update.effective_user.id)
    try:
        await update.message.reply_text("ربات مدیریت در دسترس است! 🟢")
    except Exception as e:
        print("خطا در ارسال پاسخ: ", e)

def start_manager():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("panel", start_command))
    application.add_handler(CommandHandler("start", start_command))
    
    print("ربات مدیریت راه‌اندازی شد...")
    application.run_polling()

if __name__ == '__main__':
    start_manager()
