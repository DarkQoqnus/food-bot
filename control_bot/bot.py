import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from shared.config import Config
from shared.database import db
import threading
import asyncio

bot = telebot.TeleBot(Config.BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    """دستور شروع"""
    welcome_text = """
    🍱 **ربات خرید خودکار غذا**
    
    دستورات:
    /on - شروع نظارت
    /off - توقف نظارت
    /filter - تغییر فیلتر جستجو
    /status - وضعیت فعلی
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 شروع", callback_data="start_monitor"),
        InlineKeyboardButton("🔴 توقف", callback_data="stop_monitor"),
        InlineKeyboardButton("⚙️ فیلتر", callback_data="change_filter"),
        InlineKeyboardButton("📊 وضعیت", callback_data="show_status")
    )
    
    bot.send_message(message.chat.id, welcome_text, 
                    reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['on'])
def turn_on(message):
    """شروع نظارت"""
    db.set_status("monitoring", {"is_monitoring": True})
    bot.reply_to(message, "✅ نظارت فعال شد! ربات در حال جستجوی غذا...")

@bot.message_handler(commands=['off'])
def turn_off(message):
    """توقف نظارت"""
    db.set_status("monitoring", {"is_monitoring": False})
    bot.reply_to(message, "❌ نظارت متوقف شد.")

@bot.message_handler(commands=['filter'])
def set_filter_command(message):
    """تغییر فیلتر"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("سلف", callback_data="filter_salf"),
        InlineKeyboardButton("حافظ", callback_data="filter_hafez")
    )
    bot.reply_to(message, "لطفاً فیلتر مورد نظر را انتخاب کنید:", 
                reply_markup=keyboard)

@bot.message_handler(commands=['status'])
def status_command(message):
    """نمایش وضعیت"""
    status = db.get_status("monitoring") or {
        "is_monitoring": False,
        "filter": "سلف"
    }
    
    status_text = f"""
    📊 **وضعیت ربات:**
    
    🟢 نظارت: {'فعال' if status.get('is_monitoring') else 'غیرفعال'}
    🔍 فیلتر: {status.get('filter', 'سلف')}
    👤 مدیر: {Config.ADMIN_USER_ID}
    """
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

# هندلر Callback
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "start_monitor":
        db.set_status("monitoring", {"is_monitoring": True})
        bot.answer_callback_query(call.id, "نظارت شروع شد!")
        bot.edit_message_text("✅ نظارت فعال شد!", chat_id, call.message.message_id)
    
    elif call.data == "stop_monitor":
        db.set_status("monitoring", {"is_monitoring": False})
        bot.answer_callback_query(call.id, "نظارت متوقف شد!")
        bot.edit_message_text("❌ نظارت متوقف شد.", chat_id, call.message.message_id)
    
    elif call.data == "filter_salf":
        db.set_status("monitoring", {"filter": "سلف"})
        bot.answer_callback_query(call.id, "فیلتر به 'سلف' تغییر یافت")
    
    elif call.data == "filter_hafez":
        db.set_status("monitoring", {"filter": "حافظ"})
        bot.answer_callback_query(call.id, "فیلتر به 'حافظ' تغییر یافت")
    
    elif call.data == "show_status":
        status = db.get_status("monitoring") or {"is_monitoring": False, "filter": "سلف"}
        status_text = f"وضعیت: {'فعال' if status['is_monitoring'] else 'غیرفعال'}\nفیلتر: {status['filter']}"
        bot.answer_callback_query(call.id, status_text)

def start_bot():
    """شروع کنترل‌بات"""
    print("🤖 کنترل‌بات شروع به کار کرد...")
    bot.polling(none_stop=True)
