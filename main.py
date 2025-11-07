import multiprocessing
import asyncio
from bot_manager import start_manager
from food_scraper import start_scraper

def run_bot_manager():
    """اجرای ربات مدیریت در process جداگانه"""
    start_manager()

def run_food_scraper():
    """اجرای اسکریپت اصلی در process جداگانه"""
    asyncio.run(start_scraper())

if __name__ == '__main__':
    print("🚀 در حال راه‌اندازی سیستم...")
    
    # ایجاد process ها
    manager_process = multiprocessing.Process(target=run_bot_manager)
    scraper_process = multiprocessing.Process(target=run_food_scraper)
    
    # اجرای process ها
    manager_process.start()
    scraper_process.start()
    
    print("✅ Process ها اجرا شدند")
    
    # منتظر ماندن تا process ها تمام شوند
    manager_process.join()
    scraper_process.join()
