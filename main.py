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
    def __init__(self, username, user_id, api_id=None, api_hash=None, session_string=None):
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

# ===== TELETHON CLIENT اصلی =====
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ===== TELEGRAM BOT =====
app = Application.builder().token(BOT_TOKEN).build()

# ===== HELPERS =====
def get_session(update):
    user_id = update.effective_user.id
    uname = f"@{update.effective_user.username}" if update.effective_user.username else f"user_{user_id}"
    if user_id not in admin_sessions:
        admin_sessions[user_id] = AdminSession(uname, user_id)
    return admin_sessions[user_id]

def is_admin(update):
    uname = f"@{update.effective_user.username}" if update.effective_user.username else None
    return update.effective_user and (
        update.effective_user.id == ADMIN_ID or (uname and uname in admins)
    )

async def safe_send(text):
    try:
        await app.bot.send_message(chat_id=ADMIN_ID, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await app.bot.send_message(chat_id=ADMIN_ID, text=text)
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

# ===== TELETHON EVENTS =====
@client.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):
    for session in admin_sessions.values():
        if not session.active:
            continue
        text = event.message.message or ""
        if not text:
            continue
        sender_id = event.sender_id
        if sender_id == ADMIN_ID:
            continue
        try:
            sender = await event.get_sender()
            if getattr(sender, "bot", False):
                return
        except Exception:
            return
        if match_sale(text, session.filter_words) and can_dm_seller(session, sender_id):
            send_queue.append((sender_id, "من می‌خرم ✅", session))
            session.contacted_sellers.add(sender_id)
            seller_name = f"@{sender.username}" if sender.username else f"{sender.first_name} ({sender.id})"
            await safe_send(f"به فروشنده {seller_name} پیام دادم\n📝 متن آگهی:\n{text}")

@client.on(events.NewMessage())
async def private_replies(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    if user_id == ADMIN_ID:
        return
    try:
        sender = await event.get_sender()
        if getattr(sender, "bot", False):
            return
    except Exception:
        return
    for session in admin_sessions.values():
        if user_id in session.contacted_sellers:
            msg = event.message.message or ""
            if msg:
                await asyncio.sleep(1)
                seller_name = f"@{sender.username}" if sender.username else f"{sender.first_name} ({sender.id})"
                await safe_send(f"📩 جواب از {seller_name}:\n{msg}")

# ===== COMMANDS =====
async def start(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    uname = update.effective_user.username
    name = f"@{uname}" if uname else update.effective_user.first_name
    await update.message.reply_text(f"سلام مدیر {name} 👋\nربات آماده است.")

async def toggle(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    session.toggle()
    await update.message.reply_text(f"شنود پیام‌های گروه الان {'روشن ✅' if session.active else 'خاموش ❌'} است.")

async def setfilter(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        session.set_filter(ctx.args[0])
        await update.message.reply_text(f"فیلتر مورد نظر تنظیم شد: {session.filter_words[0]}")
    else:
        await update.message.reply_text("یک کلمه بده: /setfilter سلف")

async def setcooldown(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        try:
            session.cooldown_seconds = int(ctx.args[0])
            await update.message.reply_text(f"⏱ تاخیر برای یک فروشنده تنظیم شد: {session.cooldown_seconds}")
        except ValueError:
            await update.message.reply_text("لطفاً عدد بده: /setcooldown 180")

async def setrate(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        try:
            session.global_rate_seconds = int(ctx.args[0])
            await update.message.reply_text(f"⏱ تاخیر بین فروشنده‌های مختلف تنظیم شد: {session.global_rate_seconds}")
        except ValueError:
            await update.message.reply_text("لطفاً عدد بده: /setrate 5")

async def status(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    session = get_session(update)
    st = session.status()
    status_text = "روشن ✅" if st["active"] else "خاموش ❌"
    await update.message.reply_text(
        f"📊 وضعیت ربات ({session.username}):\n"
        f"شنود: {status_text}\n"
        f"فیلتر مورد نظر: {st['filter']}\n"
        f"تاخیر برای فروشنده = {st['cooldown']}\n"
        f"تاخیر برای فروشنده های مختلف = {st['rate']}"
    )

async def send(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    if not ctx.args:
        await update.message.reply_text("فرمت درست: /send @username : پیام")
        return
    full_text = " ".join(ctx.args)
    try:
        uname, msg = full_text.split(":", 1)
        uname, msg = uname.strip(), msg.strip()
    except ValueError:
        await update.message.reply_text("فرمت درست: /send @username : پیام")
        return

    session = get_session(update)
    if not session.client:
        await update.message.reply_text("❌ کلاینت این ادمین هنوز آماده نیست.")
        return

    async def do_send():
        try:
            entity = await session.client.get_entity(uname)
            await session.client.send_message(entity.id, msg)
            await safe_send(f"✉️ پیام به {uname} فرستاده شد:\n{msg}")
        except Exception as e:
            await safe_send(f"خطا در ارسال به {uname}: {e}")

    asyncio.create_task(do_send())
    await update.message.reply_text(f"در حال ارسال به {uname} با اکانت {session.username}...")

# ===== ADMINS MANAGEMENT =====
async def list_admins(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): 
        return
    if not admins:
        await update.message.reply_text("لیست ادمین‌ها خالی است.")
        return
    # فقط یوزرنیم‌ها
    names = "\n".join(sorted(admins))
    await update.message.reply_text(f"👥 ادمین‌ها:\n{names}")

async def removeadmin(update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): 
        return
    if not ctx.args:
        await update.message.reply_text("فرمت درست: /removeadmin @username")
        return

    uname = ctx.args[0].strip()
    if not uname.startswith("@"):
        await update.message.reply_text("لطفاً یوزرنیم را با @ وارد کنید (مثلاً @amir).")
        return

    if uname not in admins:
        await update.message.reply_text("❌ همچین ادمینی در لیست نیست.")
        return

    # حذف از مجموعه‌ی admins
    admins.discard(uname)

    # پیدا کردن و پاک کردن سشن‌های متعلق به این یوزرنیم
    to_delete = []
    for uid, session in admin_sessions.items():
        if session.username == uname:
            try:
                if session.client:
                    await session.client.disconnect()
            except Exception:
                pass
            to_delete.append(uid)

    for uid in to_delete:
        del admin_sessions[uid]

    await update.message.reply_text(f"✅ ادمین {uname} حذف شد و کلاینتش بسته شد.")

    
# ===== NEWADMIN Conversation =====
USERNAME_STEP, API_ID_STEP, API_HASH_STEP, SESSION_STEP = range(4)

async def newadmin_start(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ شما دسترسی ندارید.")
        return ConversationHandler.END
    await update.message.reply_text("👤 لطفاً یوزرنیم ادمین جدید را وارد کنید (مثل @username):")
    return USERNAME_STEP

async def get_username(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["username"] = update.message.text.strip()
    await update.message.reply_text("🔑 لطفاً API_ID را وارد کنید:")
    return API_ID_STEP

async def get_api_id(update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        ctx.user_data["api_id"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ لطفاً عدد معتبر وارد کنید برای API_ID:")
        return API_ID_STEP
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

    new_session = AdminSession(uname, update.effective_user.id, api_id, api_hash, session_string)
    await new_session.init_client()

    # ثبت لیسنر روی کلاینت جدید
    @new_session.client.on(events.NewMessage(chats=GROUP_ID))
    async def group_listener(event):
        if not new_session.active:
            return
        text = event.message.message or ""
        if match_sale(text, new_session.filter_words) and can_dm_seller(new_session, event.sender_id):
            send_queue.append((event.sender_id, "من می‌خرم ✅", new_session))
            new_session.contacted_sellers.add(event.sender_id)
            await safe_send(f"ادمین {uname} به فروشنده پیام داد.")

    @new_session.client.on(events.NewMessage())
    async def private_replies(event):
        if event.is_private and event.sender_id in new_session.contacted_sellers:
            msg = event.message.message or ""
            if msg:
                await safe_send(f"📩 جواب برای {uname}: {msg}")

    admin_sessions[update.effective_user.id] = new_session
    admins.add(uname)

    await update.message.reply_text(f"✅ ادمین {uname} با کلاینت مستقل اضافه شد و شنود فعال شد.")
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

# ===== اضافه کردن همه‌ی هندلرها =====
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("toggle", toggle))
app.add_handler(CommandHandler("setfilter", setfilter))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("send", send))
app.add_handler(CommandHandler("setcooldown", setcooldown))
app.add_handler(CommandHandler("setrate", setrate))
app.add_handler(CommandHandler("admins", list_admins))
app.add_handler(get_newadmin_handler())
app.add_handler(CommandHandler("removeadmin", removeadmin))

# هندلر ساخت Session String (فایل get_session.py)
from get_session import get_conv_handler
app.add_handler(get_conv_handler())

# هندلر برای کامندهای ناشناخته
async def unknown(update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ کامند مورد نظر یافت نشد!!!")
app.add_handler(MessageHandler(filters.COMMAND, unknown))

# ===== اجرای نهایی =====
if __name__ == "__main__":
    # استارت Telethon
    client.start()
    # راه‌اندازی حلقه‌ی ارسال پیام‌ها
    asyncio.get_event_loop().create_task(sender_loop())
    # اجرای ربات تلگرام (خودش loop رو مدیریت می‌کند)
    app.run_polling()

