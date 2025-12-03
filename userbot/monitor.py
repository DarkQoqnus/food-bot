from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import logging
from datetime import datetime
from shared.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # **مهم: به خودت پیام نده! فقط لاگ کن**
            logger.info(f"📱 اکانت: @{me.username} | آی‌دی: {me.id}")
            logger.info(f"👤 مدیر: {Config.ADMIN_USER_ID}")
            logger.info(f"🎯 گروه: {Config.TARGET_GROUP_ID}")
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            logger.info("📡 ربات آماده است. برای شروع 'روشن' را بفرستید.")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا: {e}")
    
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
                await event.reply("✅ نظارت فعال شد! در حال جستجو...")
                
            elif message == "خاموش":
                self.is_monitoring = False
                logger.info("❌ نظارت متوقف شد")
                await event.reply("❌ نظارت متوقف شد")
                
            elif message == "سلف":
                self.current_filter = "سلف"
                logger.info("🔍 فیلتر: سلف")
                await event.reply("🔍 فیلتر: سلف")
                
            elif message == "حافظ":
                self.current_filter = "حافظ"
                logger.info("🔍 فیلتر: حافظ")
                await event.reply("🔍 فیلتر: حافظ")
                
            elif message == "وضعیت":
                status = "فعال ✅" if self.is_monitoring else "غیرفعال ❌"
                response = f"📊 وضعیت ربات:\n\n"
                response += f"• نظارت: {status}\n"
                response += f"• فیلتر: {self.current_filter}\n"
                response += f"• غذاهای پیدا شده: {len(self.found_items)}\n"
                response += f"• زمان شروع: {self.start_time.strftime('%H:%M:%S')}"
                
                await event.reply(response)
                
            elif message == "لیست":
                if self.found_items:
                    # آخرین ۳ غذا
                    recent = self.found_items[-3:]
                    response = "📋 آخرین غذاها:\n\n"
                    for i, item in enumerate(recent[::-1], 1):
                        time_str = item['time'].strftime('%H:%M')
                        response += f"{i}. ⏰ {time_str} | {item['filter']}\n"
                        response += f"   {item['text'][:80]}...\n\n"
                    await event.reply(response)
                else:
                    await event.reply("📭 هنوز غذایی پیدا نشده")
            
            else:
                await event.reply(
                    "🤖 دستورات:\n"
                    "• روشن - شروع\n"
                    "• خاموش - توقف\n"
                    "• سلف/حافظ - فیلتر\n"
                    "• وضعیت - اطلاعات\n"
                    "• لیست - آخرین غذاها"
                )
        
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
                logger.info(f"🍔 غذا پیدا شد! ({self.current_filter})")
                logger.info(f"   📝: {message_text[:50]}")
                logger.info(f"   👤: {sender.first_name} (آی‌دی: {sender.id})")
                
                # **ارسال پیام به فروشنده**
                seller_key = f"{sender.id}_{self.current_filter}"
                if seller_key not in self.sent_messages:
                    try:
                        # پیام به فروشنده
                        await self.client.send_message(
                            sender.id,
                            "سلام! 👋\n"
                            "خریدار غذا هستم. لطفاً:\n"
                            "• قیمت\n"
                            "• زمان تحویل\n"
                            "• محل تحویل\n\n"
                            "ممنون! 🙏"
                        )
                        
                        self.sent_messages[seller_key] = datetime.now()
                        logger.info(f"   📤 پیام به فروشنده ارسال شد")
                        
                        # گزارش به مدیر
                        await event.reply(
                            f"✅ به {sender.first_name} پیام دادم\n"
                            f"📝: {message_text[:50]}..."
                        )
                        
                    except Exception as e:
                        logger.error(f"خطا در ارسال: {e}")
                        
                        # اگر خطا داشت، فقط لاگ کن
                        if "PEER_FLOOD" in str(e):
                            logger.error("⚠️ محدودیت ارسال پیام! صبر کنید...")
                        elif "USER_BLOCKED" in str(e):
                            logger.error("⚠️ کاربر ربات را بلاک کرده")
                        elif "CHAT_WRITE_FORBIDDEN" in str(e):
                            logger.error("⚠️ امکان ارسال پیام به این کاربر نیست")

monitor = FoodMonitor()
