import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests
from datetime import datetime
from config import *

# لیست کلاینت‌های فعال
active_clients = []

def should_process_message(message_text):
    if bot_status != "on":
        return False
    
    keywords = LOCATION_FILTERS["همه"] if current_filter == "همه" else LOCATION_FILTERS[current_filter]
    return any(keyword in message_text for keyword in keywords)

async def send_quick_message(user_id, text):
    if not active_clients:
        return False
    
    for client in active_clients:
        try:
            await client.send_message(user_id, text)
            return True
        except:
            continue
    return False

async def send_report(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': YOUR_USER_ID, 'text': text}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

async def message_handler(event, account_name):
    try:
        message_text = event.message.text or ''
        message_stats["total"] += 1
        
        if should_process_message(message_text):
            sender = await event.get_sender()
            
            username = f"@{sender.username}" if sender.username else "بدون آیدی"
            user_id = sender.id
            
            success = await send_quick_message(
                sender.id, 
                "سلام! غذا رو میخرم. لطفا قیمت و جزئیات رو بفرستید. ممنون"
            )
            
            if success:
                message_stats["success"] += 1
                await send_report(
                    f"✅ پیام ارسال شد\n"
                    f"👤 به: {sender.first_name or 'ناشناس'}\n"
                    f"🆔 آیدی: {username}\n"
                    f"🤖 از: {account_name}\n"
                    f"💬 پیام: {message_text[:50]}...\n"
                    f"⏰ زمان: {datetime.now().strftime('%H:%M:%S')}"
                )
            
    except Exception as e:
        print(f"خطا در هندلر: {e}")

async def start_scraper():
    global active_clients
    
    for account in ACCOUNTS:
        if account['active'] and account.get('session_string'):
            try:
                print(f"🔗 اتصال به: {account['name']}")
                client = TelegramClient(
                    StringSession(account['session_string']),
                    API_ID,
                    API_HASH
                )
                await client.start()
                active_clients.append(client)
                
                @client.on(events.NewMessage(chats=GROUP_ID))
                async def handler(event, acc_name=account['name']):
                    await message_handler(event, acc_name)
                
                print(f"✅ {account['name']} متصل شد")
                
            except Exception as e:
                print(f"❌ خطا در {account['name']}: {e}")
    
    if not active_clients:
        print("❌ هیچ اکانت فعالی پیدا نشد")
        return
    
    await send_report(f"🤖 ربات غذا فعال شد\n\n🔄 اکانت‌های متصل: {len(active_clients)}")
    print("✅ اسکریپت اصلی فعال شد")
    
    await asyncio.gather(*[client.run_until_disconnected() for client in active_clients])
