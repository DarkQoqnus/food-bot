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
            
            # استفاده از StringSession
            session = StringSession(Config.SESSION_STRING)
            self.client = TelegramClient(session, Config.API_ID, Config.API_HASH)
            
            # اتصال
            await self.client.connect()
            
            # احراز هویت
            if not await self.client.is_user_authorized():
                logger.error("کاربر تأیید نشده! لطفاً SESSION_STRING جدید بسازید")
                return
            
            # دریافت اطلاعات کاربر
            me = await self.client.get_me()
            logger.info(f"✅ UserBot شروع به کار کرد: {me.first_name} (@{me.username})")
            
            # ارسال پیام خوشامد به مدیر
            try:
                await self.client.send_message(
                    Config.ADMIN_USER_ID,
                    f"🤖 ربات خرید غذا فعال شد!\n"
                    f"اکانت: @{me.username}\n\n"
                    f"📝 دستورات:\n"
                    f"• روشن - شروع نظارت\n"
                    f"• خاموش - توقف نظارت\n"
                    f"• سلف - جستجوی غذاهای سلف\n"
                    f"• حافظ - جستجوی غذاهای حافظ\n"
                    f"• وضعیت - نمایش وضعیت فعلی"
                )
                logger.info("پیام خوشامد به مدیر ارسال شد")
            except Exception as e:
                logger.error(f"خطا در ارسال پیام به مدیر: {e}")
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            # نگه داشتن اتصال
            logger.info("📡 در حال گوش دادن به پیام‌ها...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا در شروع یوزربات: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام"""
        
        # هندلر پیام از مدیر
        @self.client.on(events.NewMessage(from_users=Config.ADMIN_USER_ID))
        async def admin_handler(event):
            try:
                message = event.message.text.strip().lower()
                logger.info(f"پیام از مدیر: {message}")
                
                if message == "روشن":
                    self.is_monitoring = True
                    await event.reply("✅ نظارت شروع شد! در حال جستجوی غذا...")
                    logger.info("نظارت فعال شد")
                    
                elif message == "خاموش":
                    self.is_monitoring = False
                    await event.reply("❌ نظارت متوقف شد.")
                    logger.info("نظارت متوقف شد")
                    
                elif message == "سلف":
                    self.current_filter = "سلف"
                    await event.reply(f"🔍 فیلتر جستجو به 'سلف' تغییر کرد")
                    logger.info(f"فیلتر به سلف تغییر کرد")
                    
                elif message == "حافظ":
                    self.current_filter = "حافظ"
                    await event.reply(f"🔍 فیلتر جستجو به 'حافظ' تغییر کرد")
                    logger.info(f"فیلتر به حافظ تغییر کرد")
                    
                elif message == "وضعیت":
                    status = "فعال ✅" if self.is_monitoring else "غیرفعال ❌"
                    await event.reply(
                        f"📊 وضعیت ربات:\n\n"
                        f"• نظارت: {status}\n"
                        f"• فیلتر فعلی: {self.current_filter}\n"
                        f"• گروه هدف: {Config.TARGET_GROUP_ID}\n"
                        f"• اکانت: @{event.sender.username if event.sender.username else event.sender.id}"
                    )
                    
                else:
                    await event.reply(
                        "🤖 دستورات:\n"
                        "• روشن - شروع نظارت\n"
                        "• خاموش - توقف نظارت\n"
                        "• سلف/حافظ - تغییر فیلتر\n"
                        "• وضعیت - نمایش وضعیت"
                    )
                    
            except Exception as e:
                logger.error(f"خطا در پردازش پیام مدیر: {e}")
        
        # هندلر پیام از گروه
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def group_handler(event):
            try:
                if not self.is_monitoring:
                    return
                
                message_text = event.message.text or ""
                sender = await event.get_sender()
                
                logger.info(f"پیام از گروه: {message_text[:50]}")
                
                # بررسی فیلتر
                if self.current_filter in message_text:
                    logger.info(f"🍔 غذا پیدا شد! فیلتر: {self.current_filter}")
                    
                    # گزارش به مدیر
                    await self.client.send_message(
                        Config.ADMIN_USER_ID,
                        f"🔔 **غذا پیدا شد!**\n\n"
                        f"📝 پیام: {message_text[:200]}\n"
                        f"👤 فروشنده: {sender.first_name} (@{sender.username if sender.username else sender.id})\n"
                        f"🔍 فیلتر: {self.current_filter}\n"
                        f"🆔 آی‌دی: {sender.id}"
                    )
                    
                    # ارسال پیام به فروشنده
                    try:
                        await self.client.send_message(
                            sender.id,
                            "سلام! 👋\n"
                            "من خریدارم. لطفاً:\n"
                            "1. قیمت را بگویید\n"
                            "2. زمان تحویل\n"
                            "3. محل تحویل\n\n"
                            "ممنون! 🙏"
                        )
                        logger.info(f"پیام خرید به {sender.id} ارسال شد")
                        
                        # تأیید به مدیر
                        await self.client.send_message(
                            Config.ADMIN_USER_ID,
                            f"✅ پیام خرید به فروشنده ارسال شد:\n"
                            f"آی‌دی: {sender.id}\n"
                            f"نام: {sender.first_name}"
                        )
                        
                    except Exception as e:
                        logger.error(f"خطا در ارسال به فروشنده: {e}")
                        await self.client.send_message(
                            Config.ADMIN_USER_ID,
                            f"❌ خطا در ارسال پیام به فروشنده:\n{str(e)}"
                        )
                        
            except Exception as e:
                logger.error(f"خطا در پردازش پیام گروه: {e}")

monitor = FoodMonitor()
