from telegram import Update
from telegram.ext import CallbackContext
from modules.panel_manager import create_main_panel, get_panel_text
from config import YOUR_USER_ID

async def start_command(update: Update, context: CallbackContext):
    """هندلر دستور /start و /panel"""
    
    # چک کردن دسترسی کاربر
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("❌ دسترسی denied")
        return  # اینجا return میشه ولی مقدار خاصی برنمی‌گرده
    
    # ارسال پنل مدیریت
    await update.message.reply_text(
        get_panel_text(),
        reply_markup=create_main_panel(),
        parse_mode='HTML'
    )
    # اینجا هم چیزی return نمیشه
