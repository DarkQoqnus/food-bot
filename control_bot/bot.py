# control_bot/bot.py - به‌روزشده

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from shared.config import Config
from shared.database import db
import os
import time

bot = telebot.TeleBot(Config.BOT_TOKEN, parse_mode=None)

def cleanup_previous_session():
    """پاکسازی session قبلی"""
    print("🧹 پاکسازی connection‌های قبلی...")
    
    # حذف webhook اگر وجود دارد
    try:
        bot.delete_webhook()
        print("✅ Webhook قبلی حذف شد")
        time.sleep(1)
    except:
        print("ℹ️ هیچ webhook فعالی یافت نشد")
    
    # دریافت وضعیت
    try:
        webhook_info = bot.get_webhook_info()
        if webhook_info.url:
            print(f"⚠️ هنوز webhook فعال است: {webhook_info.url}")
    except:
        pass
    
    time.sleep(2)

@bot.message_handler(commands=['start'])
def start_command(message):
    """دستور شروع"""
    welcome_text = """
    🍱 **ربات خرید خودکار غذا**
    
    دستورات:
    /on - شروع نظارت
    /off - توقف نظارت
    /filter - تغییر فیلتر جستجو
    /status - وضعیت فعلی
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 شروع", callback_data="start_monitor"),
        InlineKeyboardButton("🔴 توقف", callback_data="stop_monitor"),
        InlineKeyboardButton("⚙️ فیلتر", callback_data="change_filter"),
        InlineKeyboardButton("📊 وضعیت", callback_data="show_status")
    )
    
    bot.send_message(message.chat.id, welcome_text, 
                    reply_markup=keyboard, parse_mode='Markdown')

# ... (بقیه هندلرها همانطور که قبلاً بودند)

def start_bot():
    """شروع کنترل‌بات"""
    print("🤖 کنترل‌بات شروع به کار کرد...")
    
    # پاکسازی قبل از شروع
    cleanup_previous_session()
    
    # تلاش برای شروع با retry
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 تلاش {attempt + 1} از {max_retries}...")
            
            # تست اتصال
            me = bot.get_me()
            print(f"✅ احراز هویت موفق: @{me.username}")
            
            # شروع polling با تنظیمات خاص
            bot.polling(
                none_stop=True,
                interval=2,
                timeout=20,
                skip_pending=True,  # مهم!
                allowed_updates=None,
                restart_on_change=False
            )
            break  # اگر موفق شد، حلقه را بشکن
            
        except telebot.apihelper.ApiTelegramException as e:
            if "409" in str(e):
                print(f"⚠️ خطای 409 (Conflict). صبر {retry_delay} ثانیه...")
                time.sleep(retry_delay)
                retry_delay += 2  # افزایش تاخیر
            else:
                print(f"❌ خطای دیگر: {e}")
                break
        except Exception as e:
            print(f"❌ خطای غیرمنتظره: {e}")
            break
    else:
        print("❌ تمام تلاش‌ها ناموفق بود")
