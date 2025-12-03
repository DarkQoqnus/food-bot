from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import logging
from shared.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoodMonitor:
    def __init__(self):
        self.client = None
        self.is_monitoring = False
        self.current_filter = "سلف"
    
    async def start(self):
        """شروع یوزربات"""
        try:
            if not Config.SESSION_STRING:
                logger.error("SESSION_STRING تنظیم نشده!")
                return
            
            session = StringSession(Config.SESSION_STRING)
            self.client = TelegramClient(session, Config.API_ID, Config.API_HASH)
            
            await self.client.start()
            
            # بررسی اتصال
            me = await self.client.get_me()
            logger.info(f"✅ UserBot شروع به کار کرد: @{me.username}")
            
            # ارسال پیام به مدیر
            await self.client.send_message(
                Config.ADMIN_USER_ID,
                "🤖 ربات خرید غذا فعال شد!\n\n"
                "دستورات:\n"
                "✅ روشن - شروع نظارت\n"
                "❌ خاموش - توقف نظارت\n"
                "سلف - تغییر فیلتر به سلف\n"
                "حافظ - تغییر فیلتر به حافظ\n"
                "وضعیت - نمایش وضعیت فعلی"
            )
            
            # تنظیم هندلر پیام از مدیر
            self.setup_handlers()
            
            # نگه داشتن connection
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا: {e}")
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام"""
        
        @self.client.on(events.NewMessage(chats=Config.ADMIN_USER_ID))
        async def handle_admin_message(event):
            """پردازش پیام‌های مدیر"""
            message = event.message.text.lower()
            
            if message == "روشن":
                self.is_monitoring = True
                await event.reply("✅ نظارت شروع شد!")
                
            elif message == "خاموش":
                self.is_monitoring = False
                await event.reply("❌ نظارت متوقف شد!")
                
            elif message == "سلف":
                self.current_filter = "سلف"
                await event.reply(f"🔍 فیلتر به 'سلف' تغییر کرد")
                
            elif message == "حافظ":
                self.current_filter = "حافظ"
                await event.reply(f"🔍 فیلتر به 'حافظ' تغییر کرد")
                
            elif message == "وضعیت":
                status = "فعال" if self.is_monitoring else "غیرفعال"
                await event.reply(
                    f"📊 وضعیت ربات:\n"
                    f"• نظارت: {status}\n"
                    f"• فیلتر: {self.current_filter}\n"
                    f"• گروه هدف: {Config.TARGET_GROUP_ID}"
                )
        
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def handle_group_message(event):
            """پردازش پیام‌های گروه"""
            if not self.is_monitoring:
                return
            
            message_text = event.message.text or ""
            sender_id = event.message.sender_id
            
            # بررسی فیلتر
            if self.current_filter in message_text:
                logger.info(f"🍔 غذا پیدا شد: {message_text[:50]}")
                
                # گزارش به مدیر
                await self.client.send_message(
                    Config.ADMIN_USER_ID,
                    f"🔔 غذا پیدا شد!\n\n"
                    f"📝 متن: {message_text[:100]}\n"
                    f"👤 فروشنده: {sender_id}\n"
                    f"🔍 فیلتر: {self.current_filter}"
                )
                
                # ارسال پیام به فروشنده
                try:
                    await self.client.send_message(
                        sender_id,
                        "سلام! من خریدارم. لطفاً جزییات و قیمت را بگویید."
                    )
                    logger.info(f"📤 پیام به {sender_id} ارسال شد")
                    
                    # تأیید به مدیر
                    await self.client.send_message(
                        Config.ADMIN_USER_ID,
                        f"✅ پیام خرید به فروشنده ارسال شد (آی‌دی: {sender_id})"
                    )
                    
                except Exception as e:
                    await self.client.send_message(
                        Config.ADMIN_USER_ID,
                        f"❌ خطا در ارسال پیام: {str(e)}"
                    )

monitor = FoodMonitor()
