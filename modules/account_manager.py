from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from config import *

def create_accounts_keyboard():
    keyboard = []
    for i, account in enumerate(ACCOUNTS, 1):
        status = "🟢" if account['active'] else "🔴"
        button_text = f"{account['name']} ({'فعال' if account['active'] else 'غیرفعال'})"
        keyboard.append([InlineKeyboardButton(f"{status} {button_text}", callback_data=f"account_{i}")])
    
    keyboard.append([InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_panel")])
    return InlineKeyboardMarkup(keyboard)

def get_accounts_text():
    active_count = sum(1 for acc in ACCOUNTS if acc['active'])
    text = f"👥 مدیریت اکانت‌ها\n\n📊 {active_count}/{len(ACCOUNTS)} اکانت فعال\n\n"
    
    for i, account in enumerate(ACCOUNTS, 1):
        status_icon = "🟢" if account['active'] else "🔴"
        text += f"{status_icon} {i}. {account['name']}\n"
    
    return text
