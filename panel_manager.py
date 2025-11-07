from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import *

def create_main_panel():
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="power_on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="power_off")],
        [InlineKeyboardButton("🏢 سلف", callback_data="filter_sلف"),
         InlineKeyboardButton("🏬 حافظ", callback_data="filter_حافظ")],
        [InlineKeyboardButton("👥 اکانت‌ها", callback_data="manage_accounts"),
         InlineKeyboardButton("🔄 وضعیت", callback_data="system_status")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_panel")]])

def get_panel_text():
    status_icon = "🟢" if bot_status == "on" else "🔴"
    filter_icon = "🏢" if current_filter == "سلف" else "🏬"
    
    return (
        f"🎛 پنل ربات غذا\n\n"
        f"{status_icon} وضعیت: {bot_status}\n"
        f"{filter_icon} فیلتر: {current_filter}\n"
        f"📨 پیام‌ها: {message_stats['success']}/{message_stats['total']}\n"
        f"⏰ بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    )
