from telegram import Update
from telegram.ext import CallbackContext
from config import *
from modules.panel_manager import create_main_panel, get_panel_text, create_back_button
from modules.account_manager import create_accounts_keyboard, get_accounts_text
from modules.status_manager import get_status_text

async def handle_button(update: Update, context: CallbackContext):
    """هندلر کلیه دکمه‌های اینلاین"""
    global bot_status, current_filter
    query = update.callback_query
    
    # چک دسترسی
    if query.from_user.id != YOUR_USER_ID:
        await query.answer("❌ دسترسی denied")
        return  # return بدون مقدار
    
    data = query.data
    
    # پاسخ به کلیک دکمه
    await query.answer()
    
    if data == "power_on":
        bot_status = "on"
        # پیام تایید نمایش داده میشه ولی چیزی return نمیشه
    elif data == "power_off":
        bot_status = "off"
    elif data.startswith("filter_"):
        current_filter = data.split("_")[1]
    elif data == "system_status":
        await query.edit_message_text(
            get_status_text(), 
            reply_markup=create_back_button(), 
            parse_mode='HTML'
        )
        return  # return زودهنگام
    elif data == "manage_accounts":
        await query.edit_message_text(
            get_accounts_text(),
            reply_markup=create_accounts_keyboard(),
            parse_mode='HTML'
        )
        return  # return زودهنگام
    elif data == "back_to_panel":
        await query.edit_message_text(
            get_panel_text(),
            reply_markup=create_main_panel(),
            parse_mode='HTML'
        )
        return  # return زودهنگام
    
    # آپدیت پنل اصلی
    await query.edit_message_text(
        get_panel_text(),
        reply_markup=create_main_panel(),
        parse_mode='HTML'
    )
    # اینجا هم چیزی return نمیشه
