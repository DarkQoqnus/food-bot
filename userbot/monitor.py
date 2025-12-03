from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
from shared.config import Config
from shared.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoodMonitor:
    def __init__(self):
        self.client = None
        self.is_running = False
        
    async def start(self):
        """شروع یوزربات"""
        try:
            # استفاده از session string یا ایجاد جدید
            if Config.SESSION_STRING:
                session = StringSession(Config.SESSION_STRING)
            else:
                session = "user_session"
            
            self.client = TelegramClient(
                session,
                Config.API_ID,
                Config.API_HASH
            )
            
            await self.client.start()
            logger.info("✅ UserBot شروع به کار کرد")
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            # نگه داشتن connection
            self.is_running = True
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا در شروع یوزربات: {e}")
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام"""
        
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def handler(event):
            # دریافت وضعیت از دیتابیس
            status = db.get_status("monitoring") or {
                "is_monitoring": False,
                "filter": "سلف"
            }
            
            if not status.get("is_monitoring", False):
                return
            
            current_filter = status.get("filter", "سلف")
            message_text = event.message.text or ""
            
            # بررسی فیلتر
            if current_filter in message_text:
                logger.info(f"🍔 غذا پیدا شد: {message_text[:50]}")
                
                # ارسال پیام به فروشنده
                try:
                    seller_id = event.message.sender_id
                    await self.client.send_message(
                        seller_id,
                        "سلام! من خریدارم. لطفاً جزییات و قیمت را بگویید."
                    )
                    logger.info(f"📤 پیام به {seller_id} ارسال شد")
                    
                    # گزارش به مدیر
                    await self.report_to_admin(
                        f"✅ پیام به فروشنده ارسال شد\n"
                        f"👤 فروشنده: {seller_id}\n"
                        f"📝 متن: {message_text[:100]}"
                    )
                    
                except Exception as e:
                    logger.error(f"خطا در ارسال پیام: {e}")
                    await self.report_to_admin(f"❌ خطا: {str(e)}")
    
    async def report_to_admin(self, message):
        """ارسال گزارش به مدیر"""
        try:
            await self.client.send_message(
                Config.ADMIN_USER_ID,
                f"🤖 گزارش ربات:\n{message}"
            )
        except Exception as e:
            logger.error(f"خطا در ارسال گزارش: {e}")
    
    async def stop(self):
        """توقف یوزربات"""
        if self.client:
            await self.client.disconnect()
        self.is_running = False

monitor = FoodMonitor()
