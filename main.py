import asyncio
import multiprocessing
import time
from modules.scraper_manager import start_scraper

def run_bot_manager():
    """اجرای ربات مدیریت در process جداگانه"""
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler
    from handlers import start_command, handle_button
    from config import BOT_TOKEN
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("panel", start_command))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    print("🤖 ربات مدیریت فعال شد...")
    app.run_polling()

def run_food_scraper():
    """اجرای اسکریپت اصلی"""
    asyncio.run(start_scraper())

if __name__ == '__main__':
    print("🚀 در حال راه‌اندازی سیستم...")
    
    # اجرای ربات مدیریت در process جداگانه
    bot_process = multiprocessing.Process(target=run_bot_manager)
    bot_process.start()
    
    print("✅ ربات مدیریت راه‌اندازی شد")
    
    # کمی تأخیر برای اطمینان
    time.sleep(3)
    
    # اجرای اسکریپت اصلی
    print("🔗 راه‌اندازی اسکریپت اصلی...")
    run_food_scraper()
