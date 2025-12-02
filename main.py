import asyncio
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import threading

# تنظیمات از محیط
BOT_TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
GROUP_ID = int(os.environ['GROUP_ID'])
SESSION_STRING = os.environ['SESSION_STRING']
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']

# وضعیت ربات
bot_status = "on"
current_filter = "همه"
message_count = 0

# فیلترها
FILTERS = {
    "سلف": ["سلف", "سلفی", "غذای سلف"],
    "حافظ": ["حافظ", "حافظی", "غذای حافظ"],
    "همه": ["غذا", "میفروشم", "فروش", "سلف", "حافظ"]
}

# ---- پنل مدیریت ----
def get_panel_text():
    status = "🟢 روشن" if bot_status == "on" else "🔴 خاموش"
    filter_icon = "🏢" if current_filter == "سلف" else "🏬" if current_filter == "حافظ" else "🔍"
    return f"""🎛 **کنترل ربات غذا**

{status}
{filter_icon} فیلتر: {current_filter}
📨 پیام‌های ارسالی: {message_count}"""

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="off")],
        [InlineKeyboardButton("🏢 سلف", callback_data="salf"),
         InlineKeyboardButton("🏬 حافظ", callback_data="hafez"),
         InlineKeyboardButton("🔍 همه", callback_data="all")]
    ]
    
    await update.message.reply_text(get_panel_text(), 
                                   reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='HTML')

async def button_handler(update: Update, context: CallbackContext):
    global bot_status, current_filter
    query = update.callback_query
    
    if query.from_user.id != ADMIN_ID:
        return
    
    data = query.data
    
    if data == "on":
        bot_status = "on"
        await query.answer("ربات روشن شد")
    elif data == "off":
        bot_status = "off"
        await query.answer("ربات خاموش شد")
    elif data == "salf":
        current_filter = "سلف"
        await query.answer("فیلتر: سلف")
    elif data == "hafez":
        current_filter = "حافظ"
        await query.answer("فیلتر: حافظ")
    elif data == "all":
        current_filter = "همه"
        await query.answer("فیلتر: همه")
    
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="off")],
        [InlineKeyboardButton("🏢 سلف", callback_data="salf"),
         InlineKeyboardButton("🏬 حافظ", callback_data="hafez"),
         InlineKeyboardButton("🔍 همه", callback_data="all")]
    ]
    
    await query.edit_message_text(get_panel_text(), 
                                 reply_markup=InlineKeyboardMarkup(keyboard),
                                 parse_mode='HTML')

# ---- ارسال گزارش به ادمین ----
def send_report(message):
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

# ---- مانیتورینگ و ارسال پیام ----
async def monitor_and_send():
    global message_count
    
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    
    print("🔗 در حال اتصال به تلگرام...")
    
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
        print("✅ به تلگرام وصل شد")
        
        @client.on(events.NewMessage(chats=GROUP_ID))
        async def handler(event):
            global message_count
            
            if bot_status != "on":
                return
            
            message_text = event.message.text or ""
            keywords = FILTERS[current_filter]
            
            # چک کردن فیلتر
            if any(keyword in message_text for keyword in keywords):
                try:
                    sender = await event.get_sender()
                    username = f"@{sender.username}" if sender.username else sender.first_name
                    
                    # ارسال پیام به فروشنده
                    await client.send_message(
                        sender.id,
                        "سلام! 👋\nپیام شما رو دیدم.\nمن میخرم! لطفاً قیمت و جزئیات رو بفرستید. ممنون"
                    )
                    
                    message_count += 1
                    
                    # گزارش به ادمین
                    report = f"""✅ **پیام ارسال شد**

👤 فروشنده: {username}
💬 پیام: {message_text[:50]}...
🎯 فیلتر: {current_filter}
📊 کل پیام‌ها: {message_count}"""
                    
                    send_report(report)
                    print(f"📨 پیام به {username} ارسال شد")
                    
                except Exception as e:
                    print(f"❌ خطا: {e}")
        
        print("🔍 در حال مانیتورینگ گروه...")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        send_report(f"❌ خطا در ربات: {str(e)[:100]}")

# ---- اجرای ربات ----
def main():
    # راه‌اندازی پنل مدیریت
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 ربات شروع به کار کرد...")
    print("📱 برای کنترل ربات از /panel استفاده کن")
    
    # شروع مانیتورینگ در thread جداگانه
    import threading
    monitor_thread = threading.Thread(
        target=lambda: asyncio.run(monitor_and_send()),
        daemon=True
    )
    monitor_thread.start()
    
    # اجرای ربات تلگرام
    app.run_polling()

if __name__ == "__main__":
    main()
