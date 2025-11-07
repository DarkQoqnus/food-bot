import asyncio
import os
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests

# تنظیمات
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
YOUR_USER_ID = int(os.environ['YOUR_USER_ID'])
SESSION_STRING = os.environ['SESSION_STRING']
GROUP_ID = int(os.environ['GROUP_ID'])

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def send_bot_message(text):
    """ارسال پیام به ربات مدیریت"""
    print(f"🔸 در حال ارسال پیام: {text[:50]}...")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': YOUR_USER_ID,
        'text': text,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"🔸 وضعیت ارسال: {response.status_code}")
        if response.status_code != 200:
            print(f"🔸 خطای API: {response.text}")
    except Exception as e:
        print(f"🔸 خطا در ارسال: {e}")

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    try:
        message_text = event.message.text or ''
        print(f"🔸 پیام دریافت شده: {message_text[:50]}...")
        
        if any(keyword in message_text for keyword in ['سلف', 'حافظ', 'غذا']):
            print("🔸 پیام مرتبط تشخیص داده شد")
            
            sender = await event.get_sender()
            report = f"🔔 تست: پیام از {sender.first_name}"
            
            await send_bot_message(report)
            print("🔸 گزارش ارسال شد")
            
    except Exception as e:
        print(f"🔸 خطا در هندلر: {e}")

async def main():
    await client.start()
    print("🤖 ربات شروع به کار کرد")
    
    # تست اولیه
    await send_bot_message("✅ ربات فعال شد - تست ارتباط")
    
    await client.run_until_disconnected()

if name == 'main':
    asyncio.run(main())
