from telegram import Update
from telegram.ext import CallbackContext
from config import *
from modules.panel_manager import create_main_panel, get_panel_text, create_back_button
from modules.account_manager import create_accounts_keyboard, get_accounts_text
from modules.status_manager import get_status_text

async def handle_button(update: Update, context: CallbackContext):
    global bot_status, current_filter
    query = update.callback_query
    
    if query.from_user.id != YOUR_USER_ID:
        await query.answer("❌ دسترسی denied")
        return
    
    data = query.data
    
    if data == "power_on":
        bot_status = "on"
        await query.answer("🟢 روشن شد")
    elif data == "power_off":
        bot_status = "off" 
        await query.answer("🔴 خاموش شد")
    elif data.startswith("filter_"):
        current_filter = data.split("_")[1]
        await query.answer(f"فیلتر: {current_filter}")
    elif data == "system_status":
        await query.edit_message_text(get_status_text(), reply_markup=create_back_button(), parse_mode='HTML')
        return
    elif data == "manage_accounts":
        await query.edit_message_text(get_accounts_text(), reply_markup=create_accounts_keyboard(), parse_mode='HTML')
        return
    elif data == "back_to_panel":
        await query.edit_message_text(get_panel_text(), reply_markup=create_main_panel(), parse_mode='HTML')
        return
    
    await query.edit_message_text(get_panel_text(), reply_markup=create_main_panel(), parse_mode='HTML')
