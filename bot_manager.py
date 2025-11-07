from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime
from config import *

def create_panel():
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="power_on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="power_off")],
        [InlineKeyboardButton("🏢 فیلتر: سلف", callback_data="filter_sلف")],
        [InlineKeyboardButton("🏬 فیلتر: حافظ", callback_data="filter_حافظ"),
         InlineKeyboardButton("🔍 فیلتر: همه", callback_data="filter_همه")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats"),
         InlineKeyboardButton("🔄 وضعیت", callback_data="status")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_panel_text():
    status_icon = "🟢" if bot_status == "on" else "🔴"
    filter_icon = "🏢" if current_filter == "سلف" else "🏬" if current_filter == "حافظ" else "🔍"
    
    return (
        f"🎛 پنل مدیریت ربات غذا\n\n"
        f"{status_icon} وضعیت: {bot_status}\n"
        f"{filter_icon} فیلتر: {current_filter}\n"
        f"📨 پیام‌ها: {message_stats['success']}/{message_stats['total']}\n"
        f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    )

async def start_command(update: Update, context: CallbackContext):
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    await update.message.reply_text(
        get_panel_text(),
        reply_markup=create_panel(),
        parse_mode='HTML'
    )

async def button_handler(update: Update, context: CallbackContext):
    global bot_status, current_filter
    query = update.callback_query
    
    if query.from_user.id != YOUR_USER_ID:
        await query.answer("❌ دسترسی denied", show_alert=True)
        return
    
    data = query.data
    
    if data == "power_on":
        bot_status = "on"
        await query.answer("ربات روشن شد")
    elif data == "power_off":
        bot_status = "off"
        await query.answer("ربات خاموش شد")
    elif data.startswith("filter_"):
        current_filter = data.split("_")[1]
        await query.answer(f"فیلتر: {current_filter}")
    
    await query.edit_message_text(
        get_panel_text(),
        reply_markup=create_panel(),
        parse_mode='HTML'
    )

def start_manager():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("panel", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 پنل مدیریت فعال شد...")
    app.run_polling()

if __name__ == '__main__':
    start_manager()
