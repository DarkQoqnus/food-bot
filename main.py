import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import manager_bot

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GROUP_ID = int(os.environ.get("GROUP_ID"))

# کلاینت با سشن استرینگ
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):
    # از وضعیت مشترک در manager_bot استفاده می‌کنیم
    if not manager_bot.active:
        return

    text = (event.message.message or "").strip()
    if not text:
        return

    # تطبیق ساده شامل عبارات "فروشی" و "میفروشم" برای سلف/حافظ
    for word in manager_bot.filter_words:
        if word in text:
            # اگر فقط "سلف" یا "حافظ" بود ولی فروش/فروشی نبود، رد کن
            if ("فروشی" in text) or ("میفروشم" in text) or (word.endswith("فروشی") or word.endswith("میفروشم")):
                seller_id = event.sender_id
                await client.send_message(seller_id, "من می‌خرم ✅")
                manager_bot.report_to_manager(f"به فروشنده {seller_id} پیام دادم\nمتن آگهی: {text}")
                break

@client.on(events.NewMessage())
async def private_replies(event):
    if event.is_private:
        msg = (event.message.message or "").strip()
        manager_bot.report_to_manager(f"فروشنده {event.sender_id} جواب داد: {msg}")

async def run():
    await client.start()
    # ربات مدیریت را استارت کن (non-blocking)
    manager_bot.start_manager()
    # تلثان را تا قطع شدن اجرا کن
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run())
