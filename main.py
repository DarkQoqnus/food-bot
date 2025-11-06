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
PHONE_NUMBER = '+989156707283'

async def send_bot_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

PHONE_NUMBER = '+989156707283'

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(PHONE_NUMBER)
    
    session_string = client.session.save()
    print("\n" + "="*50)
    print("SESSION_STRING شما:")
    print(session_string)
    print("="*50)
    
    await client.disconnect()

asyncio.run(main())
