import threading
import asyncio
from bot_manager import start_manager
from food_scraper import start_scraper

if __name__ == '__main__':
    # اجرای پنل مدیریت در thread جداگانه
    manager_thread = threading.Thread(target=start_manager, daemon=True)
    manager_thread.start()
    
    # اجرای اسکریپت اصلی
    asyncio.run(start_scraper())
