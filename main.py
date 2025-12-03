import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import manager_bot

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GROUP_ID = int(os.environ.get("GROUP_ID"))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):
    if not manager_bot.active:
        return

    text = (event.message.message or "").strip()
    if not text:
        return

    for word in manager_bot.filter_words:
        if word in text:
            if ("فروشی" in text) or ("میفروشم" in text) or word.endswith("فروشی") or word.endswith("میفروشم"):
                seller_id = event.sender_id
                await client.send_message(seller_id, "من می‌خرم ✅")
                await manager_bot.safe_send(f"به فروشنده {seller_id} پیام دادم\nمتن آگهی: {text}")
                break

@client.on(events.NewMessage())
async def private_replies(event):
    if event.is_private:
        msg = (event.message.message or "").strip()
        await asyncio.sleep(1)  # تاخیر برای جلوگیری از اسپم
        await manager_bot.safe_send(f"فروشنده {event.sender_id} جواب داد: {msg}")

async def run():
    await client.start()
    manager_bot.start_manager()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run())
