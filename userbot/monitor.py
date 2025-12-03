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
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            logger.info("📡 ربات آماده است. به @OxGangsteR پیام بدهید.")
            
            # **فقط یک پیام تست**
            try:
                await self.client.send_message(
                    "me",  # به Saved Messages می‌ره
                    "🤖 ربات خرید غذا فعال شد!\n"
                    "👤 اکانت: @OxGangsteR\n"
                    "🕒 زمان: " + datetime.now().strftime("%H:%M:%S") + "\n\n"
                    "دستورات:\n"
                    "• وضعیت - نمایش وضعیت\n"
                    "• روشن - شروع نظارت\n"
                    "• خاموش - توقف نظارت\n"
                    "• سلف/حافظ - تغییر فیلتر"
                )
                logger.info("✅ پیام به Saved Messages ارسال شد")
            except:
                pass
            
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام"""
        
        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def private_handler(event):
            """پردازش همه پیام‌های خصوصی"""
            sender_id = event.sender_id
            
            # فقط از مدیر
            if sender_id != Config.ADMIN_USER_ID:
                return
            
            message = event.message.text.strip().lower() if event.message.text else ""
            
            if not message:
                return
            
            logger.info(f"📩 پیام از مدیر: {message}")
            
            # پاسخ به دستورات
            if message == "روشن":
                self.is_monitoring = True
                await event.reply("✅ نظارت شروع شد!")
                logger.info("نظارت فعال شد")
                
            elif message == "خاموش":
                self.is_monitoring = False
                await event.reply("❌ نظارت متوقف شد.")
                logger.info("نظارت متوقف شد")
                
            elif message == "سلف":
                self.current_filter = "سلف"
                await event.reply("🔍 فیلتر: سلف")
                logger.info("فیلتر: سلف")
                
            elif message == "حافظ":
                self.current_filter = "حافظ"
                await event.reply("🔍 فیلتر: حافظ")
                logger.info("فیلتر: حافظ")
                
            elif message == "وضعیت":
                status = "فعال ✅" if self.is_monitoring else "غیرفعال ❌"
                response = (
                    f"📊 وضعیت ربات:\n\n"
                    f"• نظارت: {status}\n"
                    f"• فیلتر: {self.current_filter}\n"
                    f"• غذاهای پیدا شده: {len(self.found_items)}\n"
                    f"• شروع کار: {self.start_time.strftime('%H:%M')}"
                )
                await event.reply(response)
                
            elif message == "لیست":
                if self.found_items:
                    last = self.found_items[-1]
                    await event.reply(f"📝 آخرین:\n{last['text'][:100]}")
                else:
                    await event.reply("📭 غذایی پیدا نشده")
                    
            elif message == "پاکسازی":
                self.found_items = []
                self.sent_messages = {}
                await event.reply("🗑️ تاریخچه پاک شد")
                
            else:
                await event.reply(
                    "🤖 دستورات:\n"
                    "• وضعیت\n"
                    "• روشن/خاموش\n"
                    "• سلف/حافظ\n"
                    "• لیست\n"
                    "• پاکسازی"
                )
        
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def group_handler(event):
            """پردازش پیام‌های گروه"""
            if not self.is_monitoring:
                return
            
            if event.sender_id == self.bot_user_id:
                return
            
            message_text = event.message.text or ""
            
            # بررسی فیلتر
            if self.current_filter in message_text:
                sender = await event.get_sender()
                
                # ذخیره
                self.found_items.append({
                    'time': datetime.now(),
                    'text': message_text[:100],
                    'seller': sender.id,
                    'filter': self.current_filter
                })
                
                # لاگ
                logger.info(f"\n{'='*50}")
                logger.info(f"🍔 غذای {self.current_filter} پیدا شد!")
                logger.info(f"📝: {message_text[:80]}")
                logger.info(f"👤: {sender.id}")
                logger.info(f"{'='*50}")
                
                # ارسال پیام به فروشنده
                seller_key = f"{sender.id}_{self.current_filter}"
                if seller_key not in self.sent_messages:
                    try:
                        await self.client.send_message(
                            sender.id,
                            "سلام! خریدار غذا هستم.\nقیمت و جزییات؟"
                        )
                        self.sent_messages[seller_key] = datetime.now()
                        
                        # گزارش به مدیر
                        await self.client.send_message(
                            Config.ADMIN_USER_ID,
                            f"✅ به فروشنده پیام دادم\n"
                            f"آی‌دی: {sender.id}\n"
                            f"متن: {message_text[:50]}..."
                        )
                        
                        logger.info(f"✅ به {sender.id} پیام دادم")
                        
                    except Exception as e:
                        logger.error(f"خطا: {e}")

monitor = FoodMonitor()
