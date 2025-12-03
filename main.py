# main.py
from telethon import TelegramClient, events
import config
import asyncio
from manager_bot import report_to_manager

client = TelegramClient("session", config.API_ID, config.API_HASH)
client.start()

active = True
filter_words = config.FILTER_WORDS

@client.on(events.NewMessage(chats=config.GROUP_ID))
async def handler(event):
    global active, filter_words
    if not active:
        return

    text = event.message.message
    for word in filter_words:
        if word in text:
            seller_id = event.sender_id
            await client.send_message(seller_id, "من میخرم ✅")
            await report_to_manager(f"به فروشنده {seller_id} پیام دادم")
            break

@client.on(events.NewMessage())
async def reply_handler(event):
    if event.is_private:
        await report_to_manager(f"فروشنده {event.sender_id} جواب داد: {event.message.message}")

async def main():
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
