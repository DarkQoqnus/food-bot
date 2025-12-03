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
    "filter_words": ["سلف", "سلف فروشی", "سلف میفروشم", "حافظ", "حافظ فروشی", "حافظ میفروشم"],
}

# Track who we messaged + cooldowns
contacted_sellers = set()          # user_ids we DM'ed
recent_posts = set()               # message ids processed to prevent repeat
COOLDOWN_SECONDS = 60              # per seller cooldown

# ===== TELETHON CLIENT =====
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ===== TELEGRAM BOT =====
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

def is_admin(update):
    return update.effective_user and update.effective_user.id == ADMIN_ID

def start(update, context):
    if not is_admin(update):
        return
    uname = update.effective_user.username
    name = f"@{uname}" if uname else update.effective_user.first_name
    update.message.reply_text(f"سلام مدیر {name} 👋\nربات مدیریتی آماده است.")

def toggle(update, context):
    if not is_admin(update):
        return
    state["active"] = not state["active"]
    status = "روشن" if state["active"] else "خاموش"
    update.message.reply_text(f"شنود پیام‌های گروه الان {status} است.")

def setfilter(update, context):
    if not is_admin(update):
        return
    if context.args:
        state["filter_words"] = context.args
        update.message.reply_text(f"فیلترها تنظیم شد: {', '.join(state['filter_words'])}")
    else:
        update.message.reply_text("یک یا چند کلمه بده: /setfilter سلف حافظ")

async def safe_send(text):
    try:
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        # فقط لاگ کن؛ نذار کرش کنه
        print(f"Report error: {e}")

# ===== TELETHON HELPERS =====
seller_last_dm_at = {}  # user_id -> timestamp

def can_dm_seller(user_id: int) -> bool:
    import time
    t = time.time()
    last = seller_last_dm_at.get(user_id, 0)
    if t - last >= COOLDOWN_SECONDS:
        seller_last_dm_at[user_id] = t
        return True
    return False

# ===== TELETHON EVENTS =====
@client.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):
    # Only act when active
    if not state["active"]:
        return

    # Prevent repeated processing of same post
    msg_id = event.message.id
    if msg_id in recent_posts:
        return
    recent_posts.add(msg_id)

    text = (event.message.message or "").strip()
    if not text:
        return

    # Skip admin's own posts
    sender_id = event.sender_id
    if sender_id == ADMIN_ID:
        return

    # Skip bots
    try:
        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return
    except Exception:
        pass

    # Match filters
    matched = any(w in text for w in state["filter_words"])
    is_sale = ("فروشی" in text) or ("میفروشم" in text) or any(text.endswith(suf) for suf in ["فروشی", "میفروشم"])
    if matched and is_sale:
        if can_dm_seller(sender_id):
            await client.send_message(sender_id, "من می‌خرم ✅")
            contacted_sellers.add(sender_id)
            await safe_send(f"به فروشنده {sender_id} پیام دادم\nمتن آگهی: {text}")

@client.on(events.NewMessage())
async def private_replies(event):
    # Only consider replies from sellers we contacted
    if not event.is_private:
        return

    user_id = event.sender_id
    if user_id == ADMIN_ID:
        # Ignore admin's own private messages
        return

    # Skip bots
    try:
        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return
    except Exception:
        pass

    if user_id in contacted_sellers:
        msg = (event.message.message or "").strip()
        if msg:
            await asyncio.sleep(1)  # slight delay to avoid flood
            await safe_send(f"فروشنده {user_id} جواب داد: {msg}")

# ===== RUN =====
def run_bot():
    updater.start_polling()

async def run():
    await client.start()
    threading.Thread(target=run_bot, daemon=True).start()
    await client.run_until_disconnected()

# Register commands
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("toggle", toggle))
dp.add_handler(CommandHandler("setfilter", setfilter))

if __name__ == "__main__":
    asyncio.run(run())
