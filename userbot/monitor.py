from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import logging
from datetime import datetime
from shared.config import Config
import telebot  # اضافه کن برای ربات اصلی

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ربات اصلی برای اطلاع‌رسانی
bot = telebot.TeleBot(Config.BOT_TOKEN)

class FoodMonitor:
    def __init__(self):
        self.client = None
        self.is_monitoring = False
        self.current_filter = "سلف"
        self.found_items = []
        self.sent_messages = {}
        self.start_time = datetime.now()
        self.bot_user_id = None
    
    async def start(self):
        """شروع یوزربات"""
        try:
            if not Config.SESSION_STRING:
                logger.error("SESSION_STRING تنظیم نشده!")
                return
            
            session = StringSession(Config.SESSION_STRING)
            self.client = TelegramClient(session, Config.API_ID, Config.API_HASH)
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("کاربر تأیید نشده!")
                return
            
            me = await self.client.get_me()
            self.bot_user_id = me.id
            logger.info(f"✅ UserBot شروع به کار کرد: {me.first_name} (@{me.username})")
            
            # **پیام به مدیر از طریق ربات اصلی**
            try:
                bot.send_message(
                    Config.ADMIN_USER_ID,
                    f"🤖 ربات خرید غذا فعال شد!\n"
                    f"👤 اکانت: @{me.username}\n"
                    f"🕒 زمان: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"دستور 'وضعیت' را بفرستید."
                )
                logger.info("✅ پیام خوشامد ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام: {e}")
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            logger.info("📡 ربات آماده است...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام"""
        
        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and e.sender_id == Config.ADMIN_USER_ID))
        async def admin_handler(event):
            """پردازش پیام‌های مدیر"""
            message = event.message.text.strip().lower() if event.message.text else ""
            
            if not message:
                return
            
            logger.info(f"📩 دستور مدیر: {message}")
            
            if message == "روشن":
                self.is_monitoring = True
                logger.info("✅ نظارت فعال شد")
                await event.reply("✅ نظارت فعال شد!")
                bot.send_message(Config.ADMIN_USER_ID, "🔍 ربات در حال جستجوی غذا...")
                
            elif message == "خاموش":
                self.is_monitoring = False
                logger.info("❌ نظارت متوقف شد")
                await event.reply("❌ نظارت متوقف شد")
                bot.send_message(Config.ADMIN_USER_ID, "⏸️ جستجو متوقف شد")
                
            elif message == "سلف":
                self.current_filter = "سلف"
                logger.info("🔍 فیلتر: سلف")
                await event.reply("🔍 فیلتر: سلف")
                bot.send_message(Config.ADMIN_USER_ID, "🏷️ فیلتر به 'سلف' تغییر کرد")
                
            elif message == "حافظ":
                self.current_filter = "حافظ"
                logger.info("🔍 فیلتر: حافظ")
                await event.reply("🔍 فیلتر: حافظ")
                bot.send_message(Config.ADMIN_USER_ID, "🏷️ فیلتر به 'حافظ' تغییر کرد")
                
            elif message == "وضعیت":
                status = "فعال ✅" if self.is_monitoring else "غیرفعال ❌"
                response = f"📊 وضعیت:\n• نظارت: {status}\n• فیلتر: {self.current_filter}\n• غذاها: {len(self.found_items)}"
                await event.reply(response)
                
            elif message == "لیست":
                if self.found_items:
                    last = self.found_items[-1]
                    await event.reply(f"📝 آخرین:\n{last['text'][:100]}")
                else:
                    await event.reply("📭 غذایی پیدا نشده")
            
            else:
                await event.reply("❓ دستور ناشناخته. 'وضعیت' را بفرستید")
        
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def group_handler(event):
            """پردازش پیام‌های گروه"""
            if not self.is_monitoring:
                return
            
            # اگر پیام از خود ربات بود
            if event.sender_id == self.bot_user_id:
                return
            
            message_text = event.message.text or ""
            
            # اگر فیلتر در متن هست
            if self.current_filter in message_text:
                sender = await event.get_sender()
                
                # ذخیره در تاریخچه
                self.found_items.append({
                    'time': datetime.now(),
                    'text': message_text[:100],
                    'seller': sender.id,
                    'filter': self.current_filter,
                    'seller_name': sender.first_name
                })
                
                # لاگ کن
                logger.info(f"\n{'='*50}")
                logger.info(f"🚨 غذای {self.current_filter} پیدا شد!")
                logger.info(f"📝: {message_text[:80]}")
                logger.info(f"👤: {sender.first_name} (آی‌دی: {sender.id})")
                logger.info(f"{'='*50}\n")
                
                # **1. ارسال پیام به فروشنده**
                seller_key = f"{sender.id}_{self.current_filter}"
                if seller_key not in self.sent_messages:
                    try:
                        # پیام به فروشنده
                        await self.client.send_message(
                            sender.id,
                            "سلام! 👋\n"
                            "خریدار غذا هستم.\n"
                            "قیمت و جزییات لطفاً!"
                        )
                        
                        self.sent_messages[seller_key] = datetime.now()
                        
                        # **2. گزارش به مدیر از طریق ربات**
                        bot.send_message(
                            Config.ADMIN_USER_ID,
                            f"🔔 **غذا پیدا شد!**\n\n"
                            f"🏷️ نوع: {self.current_filter}\n"
                            f"📝 متن: {message_text[:100]}...\n"
                            f"👤 فروشنده: {sender.first_name}\n"
                            f"🆔 آی‌دی: {sender.id}\n\n"
                            f"✅ پیام خرید ارسال شد!"
                        )
                        
                        logger.info(f"✅ به {sender.id} پیام دادم")
                        
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"❌ خطا: {error_msg}")
                        
                        # گزارش خطا به مدیر
                        bot.send_message(
                            Config.ADMIN_USER_ID,
                            f"❌ خطا در ارسال:\n{error_msg[:200]}"
                        )

monitor = FoodMonitor()

# تابع اصلی
async def main():
    await monitor.start()

if __name__ == "__main__":
    asyncio.run(main())
