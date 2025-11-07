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
    try:
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
    except Exception as e:
        print(f"خطا در گرفتن وضعیت سیستم: {e}")
        return {
            'memory': 'نامعلوم',
            'cpu': 'نامعلوم', 
            'uptime': 'نامعلوم',
            'connection': '🟢 پایدار'
        }

def create_panel():
    """ایجاد پنل اصلی مدیریت"""
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="power_on"),
         InlineKeyboardButton("🔴 خاموش", callback_data="power_off")],
        [InlineKeyboardButton("🏢 فیلتر: سلف", callback_data="filter_sلف"),
         InlineKeyboardButton("🏬 فیلتر: حافظ", callback_data="filter_حافظ"),
         InlineKeyboardButton("🔍 فیلتر: همه", callback_data="filter_همه")],
        [InlineKeyboardButton("🔄 وضعیت سیستم", callback_data="system_status"),
         InlineKeyboardButton("👥 مدیریت اکانت‌ها", callback_data="manage_accounts")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    """ایجاد دکمه بازگشت"""
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_accounts_keyboard():
    """ایجاد کیبورد برای مدیریت اکانت‌ها"""
    keyboard = []
    
    for i, account in enumerate(ACCOUNTS, 1):
        status = "🟢" if account['active'] else "🔴"  # این خط
        button_text = f"{i}_{account['name']}: {'فعال' if account['active'] else 'غیرفعال'}"  # این خط
        callback_data = f"account_{i}"  # این خط
        keyboard.append([InlineKeyboardButton(f"{status} {button_text}", callback_data=callback_data)])  # این خط
    
    keyboard.append([InlineKeyboardButton("➕ افزودن اکانت جدید", callback_data="add_account")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_panel_text():
    """متن پنل اصلی"""
    status_icon = "🟢" if bot_status == "on" else "🔴"
    filter_icon = "🏢" if current_filter == "سلف" else "🏬" if current_filter == "حافظ" else "🔍"
    active_accounts = sum(1 for acc in ACCOUNTS if acc['active'])
    
    return (
        f"🎛 پنل مدیریت ربات غذا\n\n"
        f"{status_icon} وضعیت: {bot_status}\n"
        f"{filter_icon} فیلتر: {current_filter}\n"
        f"📨 پیام‌ها: {message_stats['success']}/{message_stats['total']}\n"
        f"👥 اکانت‌های فعال: {active_accounts}/{len(ACCOUNTS)}\n"
        f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    )

def get_accounts_text():
    """متن وضعیت اکانت‌ها"""
    active_count = sum(1 for acc in ACCOUNTS if acc['active'])
    
    text = f"👥 مدیریت اکانت‌ها\n\n"
    text += f"📊 وضعیت کلی: {active_count}/{len(ACCOUNTS)} اکانت فعال\n\n"
    
    for i, account in enumerate(ACCOUNTS, 1):

status_icon = "🟢" if account['active'] else "🔴"
        status_text = "فعال" if account['active'] else "غیرفعال"
        text += f"{status_icon} {i}. {account['name']} - {status_text}\n"
    
    text += f"\n⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    return text

async def start_command(update: Update, context: CallbackContext):
    """دستور شروع /start"""
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("❌ دسترسی denied")
        return
    
    await update.message.reply_text(
        get_panel_text(),
        reply_markup=create_panel(),
        parse_mode='HTML'
    )

async def system_status_handler(update: Update, context: CallbackContext):
    """مدیریت وضعیت سیستم"""
    query = update.callback_query
    await query.answer()
    
    # گرفتن وضعیت واقعی سیستم
    status = get_system_status()
    active_accounts = sum(1 for acc in ACCOUNTS if acc['active'])
    
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
        f"├ اکانت‌های فعال: {active_accounts}/{len(ACCOUNTS)}\n"
        f"└ آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await query.edit_message_text(
        status_text, 
        reply_markup=create_back_button(),
        parse_mode='HTML'
    )

async def manage_accounts_handler(update: Update, context: CallbackContext):
    """مدیریت نمایش لیست اکانت‌ها"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        get_accounts_text(),
        reply_markup=create_accounts_keyboard(),
        parse_mode='HTML'
    )

async def account_detail_handler(update: Update, context: CallbackContext):
    """مدیریت جزئیات اکانت"""
    query = update.callback_query
    await query.answer()
    
    try:
        account_index = int(query.data.split("_")[1]) - 1
        account = ACCOUNTS[account_index]
        
        detail_text = (
            f"👤 جزئیات اکانت\n\n"
            f"🆔 نام: {account['name']}\n"
            f"📞 شماره: {account.get('phone', 'نامشخص')}\n"
            f"🔧 وضعیت: {'🟢 فعال' if account['active'] else '🔴 غیرفعال'}\n"
            f"📅 اضافه شده: {account.get('added_date', 'نامشخص')}\n\n"
            f"⚡ عملیات:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🟢 فعال کردن", callback_data=f"enable_{account_index+1}"),
             InlineKeyboardButton("🔴 غیرفعال کردن", callback_data=f"disable_{account_index+1}")],
            [InlineKeyboardButton("🗑️ حذف اکانت", callback_data=f"delete_{account_index+1}")],
            [InlineKeyboardButton("🔙 بازگشت به مدیریت", callback_data="manage_accounts")]
        ]
        
        await query.edit_message_text(
            detail_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except IndexError:
        await query.answer("❌ اکانت پیدا نشد", show_alert=True)
        await manage_accounts_handler(update, context)

async def add_account_handler(update: Update, context: CallbackContext):
    """افزودن اکانت جدید"""
    query = update.callback_query
    await query.answer()
    
    add_account_text = (
        f"➕ افزودن اکانت جدید\n\n"
        f"📝 برای افزودن اکانت جدید، لطفاً session string رو وارد کنید:\n\n"

f"فرمت:\n"
        f"SESSION_STRING\n\n"
        f"📍 مثال:\n"
        f"1AQBz5bcdefghijklmnopqrstuvwxyz...\n\n"
        f"⚠️ توجه:\n"
        f"• از اسکریپت get_session.py برای گرفتن session string استفاده کن\n"
        f"• session string رو کپی کن و اینجا پیست کن\n"
        f"• بعد از افزودن، اکانت به لیست اضافه میشه\n\n"
        f"🔧 session string رو همینجا بفرست:"
    )
    
    await query.edit_message_text(
        add_account_text,
        reply_markup=create_back_button(),
        parse_mode='HTML'
    )

async def button_handler(update: Update, context: CallbackContext):
    """مدیریت کلیه دکمه‌ها"""
    global bot_status, current_filter
    query = update.callback_query
    
    if query.from_user.id != YOUR_USER_ID:
        await query.answer("❌ دسترسی denied", show_alert=True)
        return
    
    data = query.data
    
    try:
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
            await query.answer(f"فیلتر تغییر کرد به: {current_filter}")
            await query.edit_message_text(
                get_panel_text(),
                reply_markup=create_panel(),
                parse_mode='HTML'
            )
            
        elif data == "system_status":
            await system_status_handler(update, context)
            
        elif data == "manage_accounts":
            await manage_accounts_handler(update, context)
            
        elif data.startswith("account_"):
            await account_detail_handler(update, context)
            
        elif data.startswith("enable_"):
            account_index = int(data.split("_")[1]) - 1
            ACCOUNTS[account_index]['active'] = True
            await query.answer("✅ اکانت فعال شد")
            await manage_accounts_handler(update, context)
            
        elif data.startswith("disable_"):
            account_index = int(data.split("_")[1]) - 1
            ACCOUNTS[account_index]['active'] = False
            await query.answer("🔴 اکانت غیرفعال شد")
            await manage_accounts_handler(update, context)
            
        elif data.startswith("delete_"):
            account_index = int(data.split("_")[1]) - 1
            account_name = ACCOUNTS[account_index]['name']
            ACCOUNTS.pop(account_index)
            await query.answer(f"🗑️ اکانت {account_name} حذف شد")
            await manage_accounts_handler(update, context)
            
        elif data == "add_account":
            await add_account_handler(update, context)
            
        elif data == "back_to_panel":
            await query.edit_message_text(
                get_panel_text(),
                reply_markup=create_panel(),
                parse_mode='HTML'
            )
            
    except Exception as e:
        await query.answer(f"❌ خطا: {str(e)}", show_alert=True)
        print(f"خطا در button_handler: {e}")

def start_manager():
    """شروع ربات مدیریت"""
    try:
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
        
    except Exception as e:
        print(f"خطا در شروع ربات مدیریت: {e}")

if name == 'main':
    start_manager()
