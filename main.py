import asyncio
import logging
from telethon import TelegramClient, events
import requests

API_ID = 28175931
API_HASH = '2455aeda9d813346dd8e12d06c331e12'
BOT_TOKEN = '8280619169:AAG8E_uUJWXQ6_a_3_HooROfrCITBvIj8cI'
YOUR_USER_ID = 5669095885
GROUP_ID = -1003169743815
PHONE_NUMBER = '+989156707283'

KEYWORDS = ['سلف', 'حافظ', 'غذا', 'میفروشم']

client = TelegramClient('session', API_ID, API_HASH)

async def send_bot_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    try:
        message_text = event.message.text or ''
        sender = await event.get_sender()
        
        if any(keyword in message_text for keyword in KEYWORDS):
            report = f"🔔 پیام جدید:\n👤 {sender.first_name}\n💬 {message_text[:100]}"
            await send_bot_message(report)
            print(f"پیام تشخیص داده شد از: {sender.first_name}")
    except Exception as e:
        print(f"خطا: {e}")

async def main():
    await client.start(PHONE_NUMBER)
    await send_bot_message("🤖 ربات شروع به کار کرد")
    print("در حال مانیتورینگ...")
    await client.run_until_disconnected()

if name == '__main__':
    asyncio.run(main())
