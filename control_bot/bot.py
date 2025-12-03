import telebot
import os
import time

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "ربات فعال است")

@bot.message_handler(commands=['on'])
def on(message):
    bot.reply_to(message, "نظارت شروع شد")

@bot.message_handler(commands=['off'])
def off(message):
    bot.reply_to(message, "نظارت متوقف شد")

@bot.message_handler(commands=['filter'])
def filter_cmd(message):
    bot.reply_to(message, "فیلتر تنظیم شد")

def start_bot():
    print("🤖 شروع کنترل‌بات...")
    
    try:
        # حذف webhook قبلی
        bot.delete_webhook()
        time.sleep(1)
        
        # شروع polling
        bot.polling(
            skip_pending=True,
            none_stop=True,
            interval=2,
            timeout=20
        )
    except Exception as e:
        print(f"خطا: {e}")

if __name__ == "__main__":
    start_bot()
