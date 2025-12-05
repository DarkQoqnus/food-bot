import os, re, time, asyncio, logging
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.error import RetryAfter

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO, filename='bot.log',
                    format='%(asctime)s %(levelname)s %(message)s')

# ===== ENV =====
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
GROUP_ID = int(os.environ["GROUP_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# ===== CLASS =====
class AdminSession:
    def __init__(self, username, user_id, api_id, api_hash, session_string):
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
        self.client = TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash
        )
        await self.client.start()

        # لیسنر گروه برای همین ادمین
        @self.client.on(events.NewMessage(chats=GROUP_ID))
        async def group_listener(event):
            if not self.active:
                return
            text = event.message.message or ""
            if match_sale(text, self.filter_words) and can_dm_seller(self, event.sender_id):
                send_queue.append((event.sender_id, "من می‌خرم ✅", self))
                self.contacted_sellers.add(event.sender_id)
                seller = await event.get_sender()
                seller_name = f"@{seller.username}" if seller.username else f"{seller.first_name} ({seller.id})"
                await safe_send(f"به فروشنده {seller_name} پیام دادم\n📝 متن آگهی:\n{text}",
                                target_id=self.user_id)

        # لیسنر پیام خصوصی برای همین ادمین
        @self.client.on(events.NewMessage())
        async def private_replies(event):
            if event.is_private and event.sender_id in self.contacted_sellers:
                msg = event.message.message or ""
                if msg:
                    seller = await event.get_sender()
                    seller_name = f"@{seller.username}" if seller.username else f"{seller.first_name} ({seller.id})"
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
            "contacted_count": len(self.contacted_sellers),
            "cooldown": self.cooldown_seconds,
            "rate": self.global_rate_seconds
        }

# ===== STATE =====
admin_sessions = {}
admins = set()
send_queue = deque()
LAST_SEND_AT = 0

# ===== SENDER LOOP =====
async def sender_loop():
    global LAST_SEND_AT
    while True:
        if send_queue:
            user_id, text, session = send_queue.popleft()
            wait = max(0, session.global_rate_seconds - (time.time() - LAST_SEND_AT))
            if wait:
                await asyncio.sleep(wait)
            try:
                if session.client:
                    await session.client.send_message(user_id, text)
                    LAST_SEND_AT = time.time()
            except Exception as e:
                logging.error(f"DM error: {e}")
        else:
            await asyncio.sleep(0.5)

# ===== TELEGRAM BOT =====
app = Application.builder().token(BOT_TOKEN).build()

# ===== HELPERS =====
def get_session(update):
    return admin_sessions.get(update.effective_user.id)

def is_admin(update):
    uname = f"@{update.effective_user.username}" if update.effective_user.username else None
    return update.effective_user and (
        update.effective_user.id == ADMIN_ID or (uname and uname in admins)
    )

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
    filters_regex = r'(' + '|'.join(map(re.escape, filters)) + r')'
    has_filter = re.search(filters_regex, t)
    return bool(has_sale and has_filter)

def can_dm_seller(session, user_id: int) -> bool:
    t = time.time()
    last = session.seller_last_dm_at.get(user_id, 0)
    return (t - last) >= session.cooldown_seconds

# ===== COMMANDS =====
async def start(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    uname = update.effective_user.username
    name = f"@{uname}" if uname else update.effective_user.first_name
    await update.message.reply_text(f"سلام مدیر {name} 👋\nربات آماده است.")

async def toggle(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if not session: return
    session.toggle()
    await update.message.reply_text(f"شنود پیام‌های گروه الان {'روشن ✅' if session.active else 'خاموش ❌'} است.")

async def setfilter(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if not session: return
    if ctx.args:
        session.set_filter(ctx.args[0])
        await update.message.reply_text(f"فیلتر مورد نظر تنظیم شد: {session.filter_words[0]}")
    else:
        await update.message.reply_text("یک کلمه بده: /setfilter سلف")

async def status(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if not session: return
    st = session.status()
    status_text = "روشن ✅" if st["active"] else "خاموش ❌"
    await update.message.reply_text(
        f"📊 وضعیت ربات ({session.username}):\n"
        f"شنود: {status_text}\n"
        f"فیلتر: {st['filter']}\n"
        f"فروشنده‌های اخیر: {st['contacted_count']}\n"
        f"تاخیر فروشنده: {st['cooldown']}\n"
        f"تاخیر بین فروشنده‌ها: {st['rate']}"
    )

# ===== NEWADMIN Conversation =====
USERNAME_STEP, API_ID_STEP, API_HASH_STEP, SESSION_STEP = range(4)

async def newadmin_start(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط مدیر اصلی می‌تواند ادمین جدید اضافه کند.")
        return ConversationHandler.END
    await update.message.reply_text("👤 لطفاً یوزرنیم ادمین جدید را وارد کنید (مثل @username):")
    return USERNAME_STEP

async def get_username(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["username"] = update.message.text.strip()
    await update.message.reply_text("🔑 لطفاً API_ID را وارد کنید:")
    return API_ID_STEP

async def get_api_id(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["api_id"] = int(update.message.text.strip())
    await update.message.reply_text("🔑 لطفاً API_HASH را وارد کنید:")
    return API_HASH_STEP

async def get_api_hash(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["api_hash"] = update.message.text.strip()
    await update.message.reply_text("📜 لطفاً Session String را وارد کنید:")
    return SESSION_STEP

async def get_session_string(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uname = ctx.user_data["username"]
    api_id = ctx.user_data["api_id"]
    api_hash = ctx.user_data["api_hash"]
    session_string = update.message.text.strip()

    # ساخت سشن جدید برای ادمین
    new_session = AdminSession(uname, update.effective_user.id, api_id, api_hash, session_string)
    await new_session.init_client()

    # ذخیره در لیست سشن‌ها
    admin_sessions[update.effective_user.id] = new_session
    admins.add(uname)

    await update.message.reply_text(f"✅ ادمین {uname} اضافه شد و شنود فعال شد.")
    ctx.user_data.clear()
    return ConversationHandler.END

async def cancel_newadmin(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    await update.message.reply_text("❌ فرایند اضافه کردن ادمین لغو شد.")
    return ConversationHandler.END

def get_newadmin_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("newadmin", newadmin_start)],
        states={
            USERNAME_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            API_ID_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_id)],
            API_HASH_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_api_hash)],
            SESSION_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_session_string)],
        },
        fallbacks=[CommandHandler("cancel", cancel_newadmin)],
    )

# ===== ADMINS MANAGEMENT =====
async def list_admins(update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط مدیر اصلی می‌تواند لیست ادمین‌ها را ببیند.")
        return
    if not admins:
        await update.message.reply_text("لیست ادمین‌ها خالی است.")
        return
    names = "\n".join(sorted(admins))
    await update.message.reply_text(f"👥 ادمین‌ها:\n{names}")

async def remove_admin(update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط مدیر اصلی می‌تواند ادمین حذف کند.")
        return
    if not ctx.args:
        await update.message.reply_text("فرمت درست: /removeadmin @username")
        return

    uname = ctx.args[0].strip()
    # پیدا کردن سشن مربوطه
    to_delete = None
    for uid, s in admin_sessions.items():
        if s.username == uname:
            to_delete = uid
            break

    if not to_delete:
        await update.message.reply_text("❌ همچین ادمینی در لیست نیست.")
        return

    session = admin_sessions.pop(to_delete, None)
    admins.discard(uname)

    if session:
        try:
            if session.client:
                await session.client.disconnect()
        except Exception:
            pass

    await update.message.reply_text(f"✅ ادمین {uname} حذف شد و کلاینتش بسته شد.")

# ===== اضافه کردن همه‌ی هندلرها =====
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("toggle", toggle))
app.add_handler(CommandHandler("setfilter", setfilter))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("send", send))
app.add_handler(get_newadmin_handler())
app.add_handler(CommandHandler("admins", list_admins))
app.add_handler(CommandHandler("removeadmin", remove_admin))

# هندلر برای کامندهای ناشناخته
async def unknown(update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ کامند مورد نظر یافت نشد!!!")
app.add_handler(MessageHandler(filters.COMMAND, unknown))

# ===== اجرای نهایی =====
if __name__ == "__main__":
    # ساخت سشن مدیر اصلی
    owner_session = AdminSession("Owner", ADMIN_ID, API_ID, API_HASH, SESSION_STRING)
    asyncio.get_event_loop().run_until_complete(owner_session.init_client())
    admin_sessions[ADMIN_ID] = owner_session
    admins.add("Owner")

    asyncio.get_event_loop().create_task(sender_loop())
    app.run_polling()
