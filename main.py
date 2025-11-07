import asyncio
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import start_command, handle_button
from modules import start_scraper
from config import BOT_TOKEN

def run_bot_manager():
    """اجرای ربات مدیریت"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("panel", start_command))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    print("🤖 ربات مدیریت فعال شد...")
    app.run_polling()

def run_food_scraper():
    """اجرای اسکریپت اصلی"""
    asyncio.run(start_scraper())

def main():
    print("🚀 در حال راه‌اندازی سیستم...")
    
    # اجرای ربات مدیریت در thread جداگانه
    manager_thread = threading.Thread(target=run_bot_manager, daemon=True)
    manager_thread.start()
    
    print("✅ ربات مدیریت راه‌اندازی شد")
    
    # اجرای اسکریپت اصلی
    try:
        run_food_scraper()
    except KeyboardInterrupt:
        print("⏹️ سیستم متوقف شد")
    except Exception as e:
        print(f"❌ خطا در اجرای اسکریپت اصلی: {e}")

if __name__ == '__main__':
    main()
