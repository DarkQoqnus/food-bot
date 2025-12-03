# main.py - نسخه نهایی

import asyncio
import threading
import sys
import time
from userbot.monitor import monitor
from control_bot.bot import start_bot
from shared.config import validate_config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_userbot():
    """اجرای یوزربات"""
    print("🔧 راه‌اندازی UserBot...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(monitor.start())
    except Exception as e:
        logging.error(f"خطا در یوزربات: {e}")
        return False
    return True

def run_control_bot():
    """اجرای کنترل‌بات"""
    print("🔧 راه‌اندازی ControlBot...")
    try:
        # تاخیر بیشتر
        time.sleep(3)
        start_bot()
        return True
    except Exception as e:
        logging.error(f"خطا در کنترل‌بات: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 شروع پروژه خرید خودکار غذا")
    print("=" * 50)
    
    # اعتبارسنجی تنظیمات
    if not validate_config():
        print("❌ خطا در تنظیمات. لطفاً متغیرهای محیطی را بررسی کنید.")
        sys.exit(1)
    
    print("✅ تنظیمات اعتبارسنجی شد")
    
    # راه‌اندازی UserBot در پس‌زمینه
    print("\n1. راه‌اندازی UserBot (نظارت بر گروه)...")
    userbot_thread = threading.Thread(target=run_userbot, daemon=True)
    userbot_thread.start()
    
    # صبر برای اطمینان از راه‌اندازی UserBot
    print("⏳ صبر برای راه‌اندازی UserBot...")
    time.sleep(8)
    
    # راه‌اندازی ControlBot
    print("\n2. راه‌اندازی ControlBot (ربات مدیریت)...")
    run_control_bot()
    
    # اگر اینجا رسیدیم یعنی polling متوقف شده
    print("\n🛑 برنامه به پایان رسید")
