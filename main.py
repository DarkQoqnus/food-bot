import asyncio
from bot_manager import start_manager
from food_scraper import start_scraper
import threading

def run_bot_manager():
    """اجرای ربات مدیریت در thread جداگانه"""
    start_manager()

def run_food_scraper():
    """اجرای اسکریپت اصلی"""
    asyncio.run(start_scraper())

if name == 'main':
    print("🚀 در حال راه‌اندازی سیستم...")
    
    # اول ربات مدیریت رو در thread جداگانه اجرا کن
    manager_thread = threading.Thread(target=run_bot_manager, daemon=True)
    manager_thread.start()
    
    print("🤖 ربات مدیریت در حال راه‌اندازی...")
    
    # سپس اسکریپت اصلی رو اجرا کن
    try:
        run_food_scraper()
    except KeyboardInterrupt:
        print("⏹️ سیستم متوقف شد")
    except Exception as e:
        print(f"❌ خطا در اجرای اسکریپت اصلی: {e}")
