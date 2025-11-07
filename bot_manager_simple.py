from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

BOT_TOKEN = "8280619169:AAG8E_uUJWXQ6_a_3_HooROfrCITBvIj8cI"
YOUR_USER_ID = 5669095885

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id != YOUR_USER_ID:
        return
    
    keyboard = [
        [InlineKeyboardButton("🟢 روشن", callback_data="on")],
        [InlineKeyboardButton("🔴 خاموش", callback_data="off")]
    ]
    
    await update.message.reply_text(
        "🎛 پنل تست\n\nاین یک پنل ساده تست است",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ دکمه کار میکنه!")

def start_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Bot is running...")
    app.run_polling()

if name == 'main':
    start_bot()
