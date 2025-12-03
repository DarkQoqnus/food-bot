import asyncio
import threading
from userbot.monitor import monitor
from control_bot.bot import start_bot
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_userbot():
    """اجرای یوزربات"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor.start())

def run_control_bot():
    """اجرای کنترل‌بات"""
    start_bot()

if __name__ == "__main__":
    print("🚀 شروع پروژه خرید خودکار غذا...")
    
    # ایجاد thread برای یوزربات
    userbot_thread = threading.Thread(target=run_userbot, daemon=True)
    userbot_thread.start()
    
    # اجرای کنترل‌بات در thread اصلی
    run_control_bot()
