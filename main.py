import os, re, time, asyncio, logging
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.error import RetryAfter
from flask import Flask
from threading import Thread

# ===== وب‌سرور برای زنده نگه داشتن در رندر =====
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # رندر پورت را در محیط خود به ما می‌دهد
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# ===== ENV =====
# در رندر این متغیرها را در پنل تنظیمات وارد کنید
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
GROUP_ID = int(os.environ.get("GROUP_ID", 0))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# ===== CLASS =====
class AdminSession:
    def __init__(self, username, user_id=None, api_id=None, api_hash=None, session_string=None):
        self.username = username
        self.user_id = user_id
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.client = None
        self.active = False
        self.filter_words = []
        self.contacted_sellers = set()
        self.seller_last_dm_at = {}
        self.cooldown_seconds = 180
        self.global_rate_seconds = 5

    async def init_client(self):
        if self.api_id and self.api_hash and self.session_string:
            self.client = TelegramClient(
                StringSession(self.session_string),
                self.api_id,
                self.api_hash
            )
            await self.client.start()

            @self.client.on(events.NewMessage(chats=GROUP_ID))
            async def group_listener(event):
                if not self.active: return
                text = event.message.message or ""
                if match_sale(text, self.filter_words) and can_dm_seller(self, event.sender_id):
                    send_queue.append((event.sender_id, "من می‌خرم ✅", self))
                    self.contacted_sellers.add(event.sender_id)
                    seller = await event.get_sender()
                    seller_name = f"@{seller.username}" if seller.username else f"{seller.first_name}"
                    await safe_send(f"به فروشنده {seller_name} پیام دادم\n📝 متن آگهی:\n{text}", target_id=self.user_id)

            @self.client.on(events.NewMessage())
            async def private_replies(event):
                if event.is_private and event.sender_id in self.contacted_sellers:
                    msg = event.message.message or ""
                    if msg:
                        seller = await event.get_sender()
                        seller_name = f"@{seller.username}" if seller.username else f"{seller.first_name}"
                        await safe_send(f"📩 جواب از {seller_name}:\n{msg}", target_id=self.user_id)

    def toggle(self):
        self.active = not self.active
        return self.active

    def set_filter(self, word):
        self.filter_words = [word]

    def status(self):
        return {
            "active": self.active,
            "filter": self.filter_words[0] if self.filter_words else "-",
            "contacted_count": len(self.contacted_sellers)
        }

# ===== STATE & HELPERS =====
admin_sessions_by_user_id = {}
admin_sessions_by_username = {}
admins = set()
send_queue = deque()
LAST_SEND_AT = 0

def get_session(update):
    user_id = update.effective_user.id
    uname = f"@{update.effective_user.username}" if update.effective_user.username else None
    if user_id in admin_sessions_by_user_id: return admin_sessions_by_user_id[user_id]
    if uname and uname in admin_sessions_by_username:
        s = admin_sessions_by_username[uname]
        s.user_id = user_id
        admin_sessions_by_user_id[user_id] = s
        return s
    return None

def is_admin(update):
    uname = f"@{update.effective_user.username}" if update.effective_user.username else None
    return update.effective_user and (update.effective_user.id == ADMIN_ID or (uname and uname in admins))

async def safe_send(text, target_id):
    try:
        await app.bot.send_message(chat_id=target_id, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await app.bot.send_message(chat_id=target_id, text=text)
    except Exception as e:
        logging.error(f"Report error: {e}")

def normalize_text(t): 
    t = (t or "").replace('\u200c', ' ').strip()
    t = re.sub(r'\s+', ' ', t)
    t = t.replace('ي','ی').replace('ك','ک')
    return t

def match_sale(text, filters):
    t = normalize_text(text)
    has_sale = re.search(r'(فروشی|می[\s\u200c]*فروشم)', t)
    if not filters: return False
    filters_regex = r'(' + '|'.join(map(re.escape, filters)) + r')'
    has_filter = re.search(filters_regex, t)
    return bool(has_sale and has_filter)

def can_dm_seller(session, user_id: int) -> bool:
    t = time.time()
    last = session.seller_last_dm_at.get(user_id, 0)
    return (t - last) >= session.cooldown_seconds

async def sender_loop():
    global LAST_SEND_AT
    while True:
        if send_queue:
            user_id, text, session = send_queue.popleft()
            wait = max(0, session.global_rate_seconds - (time.time() - LAST_SEND_AT))
            if wait: await asyncio.sleep(wait)
            try:
                if session.client:
                    await session.client.send_message(user_id, text)
                    LAST_SEND_AT = time.time()
                    session.seller_last_dm_at[user_id] = time.time()
            except Exception as e:
                logging.error(f"DM error: {e}")
        await asyncio.sleep(0.5)

# ===== TELEGRAM BOT =====
app = Application.builder().token(BOT_TOKEN).build()

# اینجا دستورات (start, toggle, setfilter و ...) رو طبق کد قبلی خودت اضافه کن
async def start(update, ctx):
    if is_admin(update): await update.message.reply_text("ربات آماده است ✅")

app.add_handler(CommandHandler("start", start))
# بقیه هندلرها رو هم مثل کد خودت اینجا اضافه کن...

# ===== اجرای نهایی =====
async def main():
    # ۱. روشن کردن وب‌سرور برای رندر
    keep_alive()
    print("🌐 Web Server Started for Render compatibility.")

    # ۲. راه اندازی کلاینت مدیریت
    owner_session = AdminSession("Owner", ADMIN_ID, API_ID, API_HASH, SESSION_STRING)
    await owner_session.init_client()
    admin_sessions_by_user_id[ADMIN_ID] = owner_session
    admins.add("Owner")

    # ۳. اجرای حلقه‌ها و بات
    asyncio.create_task(sender_loop())
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("🤖 Telegram Bot is Polling...")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
