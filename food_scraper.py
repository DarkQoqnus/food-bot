from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests
from config import *

# اول client رو تعریف کن، بعد هندلر
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def should_process_message(message_text):
    if bot_status != "on":
        return False
    
    keywords = LOCATION_FILTERS["همه"] if current_filter == "همه" else LOCATION_FILTERS[current_filter]
    return any(keyword in message_text for keyword in keywords)

async def send_quick_message(user_id, text):
    try:
        await client.send_message(user_id, text)
        return True
    except:
        return False

async def send_report(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# حالا هندلر رو تعریف کن - بعد از تعریف client
@client.on(events.NewMessage(chats=GROUP_ID))
async def message_handler(event):
    try:
        message_text = event.message.text or ''
        message_stats["total"] += 1
        
        if should_process_message(message_text):
            sender = await event.get_sender()
            
            # گرفتن آیدی کاربر
            username = f"@{sender.username}" if sender.username else "بدون آیدی"
            user_id = sender.id
            
            success = await send_quick_message(
                sender.id, 
                "سلام! غذا رو میخرم. لطفا قیمت و جزئیات رو بفرستید. ممنون"
            )
            
            if success:
                message_stats["success"] += 1
                await send_report(
                    f"✅ پیام ارسال شد به:\n"
                    f"👤 نام: {sender.first_name or 'ناشناس'}\n"
                    f"🆔 آیدی: {username}\n"
                    f"💬 پیام: {message_text[:50]}..."
                )
            else:
                await send_report(f"❌ خطا در ارسال به {username}")
            
    except Exception as e:
        print(f"خطا: {e}")

async def start_scraper():
    await client.start()
    await send_report("🤖 ربات غذا فعال شد - از /panel استفاده کن")
    print("✅ اسکریپت اصلی فعال شد")
    await client.run_until_disconnected()
