import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests

# خواندن از Environment Variables
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
YOUR_USER_ID = int(os.environ['YOUR_USER_ID'])
SESSION_STRING = os.environ['SESSION_STRING']
GROUP_ID = int(os.environ['GROUP_ID'])

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def send_bot_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload)
    except:
        pass

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    try:
        message_text = event.message.text or ''
        if any(keyword in message_text for keyword in ['سلف', 'حافظ', 'غذا']):
            sender = await event.get_sender()
            report = f"🔔 پیام جدید از {sender.first_name}: {message_text[:100]}"
            await send_bot_message(report)
    except Exception as e:
        print(f"خطا: {e}")

async def main():
    await client.start()
    await send_bot_message("🤖 ربات شروع به کار کرد")
    print("در حال مانیتورینگ...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
