import os
import asyncio
import threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import Updater, CommandHandler
from telegram.error import RetryAfter

# ===== ENV =====
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GROUP_ID = int(os.environ.get("GROUP_ID"))
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# ===== STATE =====
state = {
    "active": True,
    "filter_words": [
        "سلف", "سلف فروشی", "سلف میفروشم",
        "حافظ", "حافظ فروشی", "حافظ میفروشم",
    ],
}

# ===== TELETHON CLIENT =====
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ===== TELEGRAM BOT =====
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

def is_admin(update):
    return update.effective_user and update.effective_user.id == ADMIN_ID

def start(update, context):
    if not is_admin(update): return
    update.message.reply_text("مدیریت ربات فعال شد ✅")

def toggle(update, context):
    if not is_admin(update): return
    state["active"] = not state["active"]
    status = "روشن" if state["active"] else "خاموش"
    update.message.reply_text(f"شنود پیام‌ها الان {status} است")

def setfilter(update, context):
    if not is_admin(update): return
    if context.args:
        state["filter_words"] = context.args
        update.message.reply_text(f"فیلترها تنظیم شد: {', '.join(state['filter_words'])}")
    else:
        update.message.reply_text("لطفاً یک یا چند کلمه بده: /setfilter سلف حافظ")

async def safe_send(text):
    try:
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Report error: {e}")

# ===== TELETHON EVENTS =====
@client.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):
    if not state["active"]:
        return
    text = (event.message.message or "").strip()
    if not text: return
    for word in state["filter_words"]:
        if word in text:
            if ("فروشی" in text) or ("میفروشم" in text) or word.endswith("فروشی") or word.endswith("میفروشم"):
                seller_id = event.sender_id
                await client.send_message(seller_id, "من می‌خرم ✅")
                await safe_send(f"به فروشنده {seller_id} پیام دادم\nمتن آگهی: {text}")
                break

@client.on(events.NewMessage())
async def private_replies(event):
    if event.is_private:
        msg = (event.message.message or "").strip()
        await asyncio.sleep(1)  # تاخیر برای جلوگیری از اسپم
        await safe_send(f"فروشنده {event.sender_id} جواب داد: {msg}")

# ===== RUN =====
def run_bot():
    updater.start_polling()

async def run():
    await client.start()
    # اجرای ربات مدیریتی در Thread جدا
    threading.Thread(target=run_bot, daemon=True).start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run())
