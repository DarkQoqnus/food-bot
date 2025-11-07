import asyncio
import os
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

async def send_quick_message(user_id, text):
    """ارسال سریع پیام بدون تأخیر"""
    try:
        await client.send_message(user_id, text)
        return True
    except Exception as e:
        return False

async def send_bot_message(text):
    """گزارش‌دهی غیرهمزمان"""
    # غیرفعال موقت برای سرعت
    pass

@client.on(events.NewMessage(chats=GROUP_ID))
async def ultra_fast_handler(event):
    try:
        message_text = event.message.text or ''
        
        # چک سریع با کمترین پردازش
        if 'سلف' in message_text or 'حافظ' in message_text or 'غذا' in message_text:
            sender = await event.get_sender()
            
            # فوراً پیام بفرست
            success = await send_quick_message(
                sender.id, 
                "سلام! غذا رو میخرم. لطفا قیمت و جزئیات رو بفرستید. ممنون"
            )
            
            # سپس گزارش بده
            if success:
                report = f"✅ سریع پیام دادم به: {sender.first_name}"
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {'chat_id': YOUR_USER_ID, 'text': report}
                requests.post(url, json=payload)
            
    except Exception as e:
        print(f"خطا: {e}")

async def main():
    await client.start()
    print("⚡ ربات فوق‌سریع فعال شد!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
