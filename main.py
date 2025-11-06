import asyncio
import os
from telethon import TelegramClient, events
import requests

# تنظیمات
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
YOUR_USER_ID = int(os.environ['YOUR_USER_ID'])
GROUP_ID = int(os.environ['GROUP_ID'])

# لیست شماره‌ها (می‌تونی بعداً اضافه کنی)
PHONE_NUMBERS = [
    '+989156707283'
]

clients = []

async def send_bot_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

async def init_accounts():
    for i, phone in enumerate(PHONE_NUMBERS):
        try:
            client = TelegramClient(f'session_{i}', API_ID, API_HASH)
            await client.start(phone)
            clients.append(client)
            await send_bot_message(f"✅ اکانت {i+1} وصل شد")
            
            # هندلر برای هر کلاینت
            @client.on(events.NewMessage(chats=GROUP_ID))
            async def handler(event):
                try:
                    msg = event.message.text or ''
                    if any(kw in msg for kw in ['سلف', 'حافظ', 'غذا']):
                        sender = await event.get_sender()
                        report = f"🔔 پیام از {sender.first_name}:\n{msg[:100]}"
                        await send_bot_message(report)
                except Exception as e:
                    print(f"خطا: {e}")
                    
        except Exception as e:
            await send_bot_message(f"❌ خطا در اکانت {i+1}: {str(e)[:100]}")

async def main():
    await send_bot_message("🚀 در حال راه‌اندازی...")
    await init_accounts()
    await send_bot_message("🤖 ربات آماده است!")
    
    # منتظر ماندن
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main':
    asyncio.run(main())
