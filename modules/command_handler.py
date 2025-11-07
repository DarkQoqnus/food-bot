from telegram import Update
from telegram.ext import CallbackContext
from modules.panel_manager import create_main_panel, get_panel_text

async def start_command(update: Update, context: CallbackContext):
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("❌ دسترسی denied")
        return
    
    await update.message.reply_text(
        get_panel_text(),
        reply_markup=create_main_panel(),
        parse_mode='HTML'
    )
