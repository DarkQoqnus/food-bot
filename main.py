import asyncio
import os
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests
from datetime import datetime
import time

# خواندن از متغیرهای محیطی
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
YOUR_USER_ID = int(os.environ['YOUR_USER_ID'])
SESSION_STRING = os.environ['SESSION_STRING']
GROUP_ID = int(os.environ['GROUP_ID'])

# تنظیمات
MAX_MESSAGES_PER_MINUTE = 3
MAX_MESSAGES_PER_HOUR = 20
CURRENT_FILTER = "همه"  # سلف / حافظ / همه

# کلمات کلیدی
LOCATION_FILTERS = {
    "سلف": ["سلف", "سلفی", "غذای سلف", "سلف دانشگاه", "سلف اصلی"],
    "حافظ": ["حافظ", "حافظی", "غذای حافظ", "رستوران حافظ", "حافظ مرکزی"],
    "همه": ["فروش", "غذا", "میفروشم", "فروشی", "سلف", "حافظ"]
}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def send_bot_message(text):
    """ارسال پیام به ربات مدیریت"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': YOUR_USER_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال به ربات: {e}")

def should_process_message(message_text):
    """بررسی اینکه پیام باید پردازش شود یا نه"""
    if CURRENT_FILTER == "همه":
        return any(keyword in message_text for keyword in LOCATION_FILTERS["همه"])
    else:
        filter_keywords = LOCATION_FILTERS.get(CURRENT_FILTER, [])
        return any(keyword in message_text for keyword in filter_keywords)

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    try:
        message = event.message
        message_text = message.text or ''
        sender = await event.get_sender()
        
        if should_process_message(message_text):
            print(f"🔍 پیام تشخیص داده شد از {sender.first_name}")
            
            # ارسال گزارش
            report = f"""
🔔 <b>پیام جدید تشخیص داده شد</b>

👤 <b>فرستنده:</b> {sender.first_name or 'ناشناس'}
💬 <b>پیام:</b> {message_text[:100]}...
🏢 <b>فیلتر:</b> {CURRENT_FILTER}
⏰ <b>زمان:</b> {datetime.now().strftime('%H:%M:%S')}

✅ <i>آماده ارسال پیام</i>
"""
            await send_bot_message(report)
            
    except Exception as e:
        error_msg = f"❌ خطا در پردازش پیام: {e}"
        print(error_msg)
        await send_bot_message(error_msg)

async def main():
    await client.start()
    await send_bot_message("🤖 <b>ربات فروش غذا شروع به کار کرد</b>")
    print("✅ ربات شروع به کار کرد و در حال مانیتورینگ...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
