import os, re, time, asyncio, threading, logging
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import Updater, CommandHandler
from telegram.error import RetryAfter
from telegram.ext import MessageHandler, Filters

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO, filename='bot.log',
                    format='%(asctime)s %(levelname)s %(message)s')

# ===== ENV =====
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
GROUP_ID = int(os.environ["GROUP_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])  # ادمین اصلی (ID عددی تو)

# ===== CLASS =====
class AdminSession:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.active = False
        self.filter_words = []
        self.contacted_sellers = set()
        self.seller_last_dm_at = {}
        self.cooldown_seconds = 180   # دیفالت 180 ثانیه
        self.global_rate_seconds = 5

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
admins = set()  # لیست یوزرنیم‌ها، مدیریت فقط توسط ADMIN_ID اصلی
send_queue = deque()
LAST_SEND_AT = 0

# ===== TELETHON CLIENT =====
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ===== TELEGRAM BOT =====
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

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

# ===== COMMANDS =====
def start(update, ctx):
    if not is_admin(update): return
    uname = update.effective_user.username
    name = f"@{uname}" if uname else update.effective_user.first_name
    update.message.reply_text(f"سلام مدیر {name} 👋\nربات آماده است.")

def toggle(update, ctx):
    if not is_admin(update): return
    session = get_session(update)
    session.toggle()
    update.message.reply_text(f"شنود پیام‌های گروه الان {'روشن ✅' if session.active else 'خاموش ❌'} است.")

def setfilter(update, ctx):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        session.set_filter(ctx.args[0])
        update.message.reply_text(f"فیلتر مورد نظر تنظیم شد: {session.filter_words[0]}")
    else:
        update.message.reply_text("یک کلمه بده: /setfilter سلف")

def setcooldown(update, ctx):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        try:
            session.cooldown_seconds = int(ctx.args[0])
            update.message.reply_text(f"⏱ تاخیر برای یک فروشنده تنظیم شد: {session.cooldown_seconds}")
        except ValueError:
            update.message.reply_text("لطفاً عدد بده: /setcooldown 180")

def setrate(update, ctx):
    if not is_admin(update): return
    session = get_session(update)
    if ctx.args:
        try:
            session.global_rate_seconds = int(ctx.args[0])
            update.message.reply_text(f"⏱ تاخیر بین فروشنده‌های مختلف تنظیم شد: {session.global_rate_seconds}")
        except ValueError:
            update.message.reply_text("لطفاً عدد بده: /setrate 5")

def status(update, ctx):
    if not is_admin(update): return
    session = get_session(update)
    st = session.status()
    status_text = "روشن ✅" if st["active"] else "خاموش ❌"
    update.message.reply_text(
        f"📊 وضعیت ربات ({session.username}):\n"
        f"شنود: {status_text}\n"
        f"فیلتر مورد نظر: {st['filter']}\n"
        f"فروشنده‌های اخیر: {st['contacted_count']}\n"
        f"COOLDOWN_SECONDS = {st['cooldown']}\n"
        f"GLOBAL_RATE_SECONDS = {st['rate']}"
    )

def send(update, ctx):
    if not is_admin(update): return
    if not ctx.args:
        update.message.reply_text("فرمت درست: /send @username : پیام")
        return
    full_text = " ".join(ctx.args)
    try:
        uname, msg = full_text.split(":", 1)
        uname, msg = uname.strip(), msg.strip()
    except ValueError:
        update.message.reply_text("فرمت درست: /send @username : پیام")
        return

    async def do_send():
        try:
            entity = await client.get_entity(uname)
            await client.send_message(entity.id, msg)
            await safe_send(f"✉️ پیام به {uname} فرستاده شد:\n{msg}")
        except Exception as e:
            await safe_send(f"خطا در ارسال به {uname}: {e}")

    asyncio.create_task(do_send())
    update.message.reply_text(f"در حال ارسال به {uname}...")

def newadmin(update, ctx):
    if update.effective_user.id != ADMIN_ID:  # فقط ادمین اصلی
        return
    if not ctx.args:
        update.message.reply_text("فرمت درست: /newadmin @username")
        return
    uname = ctx.args[0].strip()
    admins.add(uname)
    update.message.reply_text(f"✅ {uname} به لیست ادمین‌ها اضافه شد.")

def removeadmin(update, ctx):
    if update.effective_user.id != ADMIN_ID:  # فقط ادمین اصلی
        return
    if not ctx.args:
        update.message.reply_text("فرمت درست: /removeadmin @username")
        return
    uname = ctx.args[0].strip()
    if uname in admins:
        admins.remove(uname)
        update.message.reply_text(f"❌ {uname} از لیست ادمین‌ها حذف شد.")
    else:
        update.message.reply_text(f"{uname} در لیست ادمین‌ها نبود.")

def list_admins(update, ctx):
    if update.effective_user.id != ADMIN_ID:  # فقط ادمین اصلی
        return
    if not admins:
        update.message.reply_text("هیچ ادمینی ثبت نشده.")
        return
    text = "👥 لیست ادمین‌ها:\n"
    for i, uname in enumerate(admins, start=1):
        text += f"{i} - {uname}\n"
    update.message.reply_text(text)

def unknown(update, ctx):
    update.message.reply_text("❌ کامند مورد نظر یافت نشد!!!")

# ===== HELPERS =====
async def safe_send(text):
    try:
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        updater.bot.send_message(chat_id=ADMIN_ID, text=text)
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
    if t - last >= session.cooldown_seconds:
        return True
    return False

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
                await client.send_message(user_id, text)
                LAST_SEND_AT = time.time()
            except Exception as e:
                logging.error(f"DM error: {e}")
        else:
            await asyncio.sleep(0.5)

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

# ===== RUN =====
def run_bot():
    updater.start_polling()

async def run():
    await client.start()
    threading.Thread(target=run_bot, daemon=True).start()
    asyncio.create_task(sender_loop())
    await client.run_until_disconnected()

# ===== HANDLERS =====
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("toggle", toggle))
dp.add_handler(CommandHandler("setfilter", setfilter))
dp.add_handler(CommandHandler("status", status))
dp.add_handler(CommandHandler("send", send))

# دستورات مدیریت ضداسپم
dp.add_handler(CommandHandler("setcooldown", setcooldown))
dp.add_handler(CommandHandler("setrate", setrate))

# دستورات مدیریت ادمین‌ها (فقط ادمین اصلی)
dp.add_handler(CommandHandler("newadmin", newadmin))
dp.add_handler(CommandHandler("removeadmin", removeadmin))
dp.add_handler(CommandHandler("admins", list_admins))

# هندلر برای کامندهای ناشناخته
dp.add_handler(MessageHandler(Filters.command, unknown))

if __name__ == "__main__":
    asyncio.run(run())
