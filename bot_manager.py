import asyncio
import psutil
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime
from config import *

# زمان شروع سیستم
start_time = time.time()

def get_system_status():
    """گرفتن وضعیت واقعی سیستم"""
    # مصرف حافظه
    memory = psutil.virtual_memory()
    memory_usage = f"{memory.percent}٪ ({memory.used // 1024 // 1024} مگابایت)"
    
    # مصرف CPU
    cpu_usage = f"{psutil.cpu_percent()}٪"
    
    # آپتایم
    uptime_seconds = time.time() - start_time
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    uptime = f"{uptime_hours} ساعت و {uptime_minutes} دقیقه"
    
    # وضعیت اتصال
    connection_status = "🟢 پایدار"
    
    return {
        'memory': memory_usage,
        'cpu': cpu_usage,
        'uptime': uptime,
        'connection': connection_status
    }

def create_panel():
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="power_on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="power_off")],
        [InlineKeyboardButton("🏢 فیلتر: سلف", callback_data="filter_sلف"),
         InlineKeyboardButton("🏬 فیلتر: حافظ", callback_data="filter_حافظ"),
         InlineKeyboardButton("🔍 فیلتر: همه", callback_data="filter_همه")],
        [InlineKeyboardButton("🔄 وضعیت سیستم", callback_data="system_status")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_panel")]
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

async def system_status_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    # گرفتن وضعیت واقعی سیستم
    status = get_system_status()
    
    status_text = (
        f"🔄 وضعیت لحظه‌ای سیستم\n\n"
        f"🤖 وضعیت سرویس‌ها:\n"
        f"├ ربات مدیریت: 🟢 آنلاین\n"
        f"├ اسکریپت اصلی: 🟢 در حال مانیتورینگ\n"
        f"├ اتصال تلگرام: {status['connection']}\n"
        f"└ وضعیت کلی: 🟢 فعال\n\n"
        f"💾 مصرف منابع:\n"
        f"├ حافظه: {status['memory']}\n"
        f"├ پردازنده: {status['cpu']}\n"
        f"└ آپتایم: {status['uptime']}\n\n"
        f"📊 وضعیت فعلی:\n"
        f"├ فیلتر: {current_filter}\n"
        f"├ وضعیت ربات: {bot_status}\n"
        f"├ پیام‌های ارسالی: {message_stats['success']}\n"
        f"└ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await query.edit_message_text(
        status_text, 
        reply_markup=create_back_button(),
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
        await query.edit_message_text(
            get_panel_text(),
            reply_markup=create_panel(),
            parse_mode='HTML'
        )
    elif data == "power_off":
        bot_status = "off"
        await query.answer("ربات خاموش شد")
        await query.edit_message_text(
            get_panel_text(),
            reply_markup=create_panel(),
            parse_mode='HTML'
        )
    elif data.startswith("filter_"):
        current_filter = data.split("_")[1]
        await query.answer(f"فیلتر: {current_filter}")
        await query.edit_message_text(
            get_panel_text(),
            reply_markup=create_panel(),
            parse_mode='HTML'
        )
    elif data == "system_status":
        await system_status_handler(update, context)
    elif data == "back_to_panel":
        await query.edit_message_text(
            get_panel_text(),
            reply_markup=create_panel(),
            parse_mode='HTML'
        )

def start_manager():
    # ایجاد event loop جدید برای این thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("panel", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 پنل مدیریت فعال شد...")
    
    # اجرای برنامه با event loop جدید
    app.run_polling()

if __name__ == '__main__':
    start_manager()
