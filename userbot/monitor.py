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
        self.bad_words = []
        self.found_items = []
        self.sent_messages = {}
        self.start_time = datetime.now()
        self.bot_user_id = None  # آی‌دی عددی خود ربات
    
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
            
            # دریافت اطلاعات اکانت
            me = await self.client.get_me()
            self.bot_user_id = me.id  # ذخیره آی‌دی ربات
            logger.info(f"✅ UserBot شروع به کار کرد: {me.first_name} (آی‌دی: {me.id})")
            
            # فقط یک پیام تست به مدیر
            try:
                await self.client.send_message(
                    Config.ADMIN_USER_ID,
                    "✅ ربات فعال شد. دستور 'وضعیت' را بفرستید."
                )
            except:
                pass  # مهم نیست اگر نرسید
            
            # تنظیم هندلرها
            self.setup_handlers()
            
            logger.info("📡 در حال گوش دادن...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"خطا: {e}")
    
    def setup_handlers(self):
        """تنظیم هندلرهای پیام - فقط به دستورات مستقیم پاسخ دهد"""
        
        # **فقط وقتی مستقیم به خود ربات پیام می‌دهید**
        @self.client.on(events.NewMessage(pattern='^(?i)(روشن|خاموش|سلف|حافظ|وضعیت|لیست|حذف فیلتر)'))
        async def direct_command_handler(event):
            """هندلر دستورات مستقیم"""
            # بررسی کن که پیام مستقیم به خود ربات است
            if event.is_private and event.sender_id == Config.ADMIN_USER_ID:
                message = event.message.text.strip().lower()
                logger.info(f"🔧 دستور مستقیم: {message}")
                
                if message == "روشن":
                    self.is_monitoring = True
                    await event.reply("✅ نظارت شروع شد!")
                    
                elif message == "خاموش":
                    self.is_monitoring = False
                    await event.reply("❌ نظارت متوقف شد.")
                    
                elif message == "سلف":
                    self.current_filter = "سلف"
                    await event.reply("🔍 فیلتر: سلف")
                    
                elif message == "حافظ":
                    self.current_filter = "حافظ"
                    await event.reply("🔍 فیلتر: حافظ")
                    
                elif message == "وضعیت":
                    status = "فعال" if self.is_monitoring else "غیرفعال"
                    await event.reply(f"📊 وضعیت:\n• نظارت: {status}\n• فیلتر: {self.current_filter}")
                    
                elif message == "لیست":
                    if self.found_items:
                        last = self.found_items[-1] if self.found_items else {}
                        await event.reply(f"📝 آخرین غذا: {last.get('text', 'ندارد')[:100]}")
                    else:
                        await event.reply("📭 غذایی پیدا نشده")
                
                elif "حذف فیلتر" in message:
                    await event.reply("⚙️ این قابلیت بعداً اضافه می‌شود")
        
        # **هندلر گروه - فقط پیام‌های گروه را بررسی کند**
        @self.client.on(events.NewMessage(chats=Config.TARGET_GROUP_ID))
        async def group_handler(event):
            """فقط پیام‌های گروه هدف"""
            if not self.is_monitoring:
                return
            
            message_text = event.message.text or ""
            
            # اگر پیام از خود ربات بود، نادیده بگیر
            if event.sender_id == self.bot_user_id:
                return
            
            # بررسی فیلتر
            if self.current_filter in message_text:
                sender = await event.get_sender()
                
                # ذخیره در تاریخچه
                self.found_items.append({
                    'time': datetime.now(),
                    'text': message_text[:150],
                    'seller': sender.id,
                    'filter': self.current_filter
                })
                
                # لاگ ساده
                logger.info(f"🍔 غذا پیدا شد: {self.current_filter} - {message_text[:50]}")
                
                # گزارش به مدیر
                try:
                    await self.client.send_message(
                        Config.ADMIN_USER_ID,
                        f"🔔 غذا پیدا شد ({self.current_filter})\n"
                        f"📝: {message_text[:100]}..."
                    )
                except:
                    pass  # اگر نرسید مهم نیست
                
                # ارسال پیام به فروشنده (فقط یک بار)
                seller_key = f"{sender.id}_{self.current_filter}"
                if seller_key not in self.sent_messages:
                    try:
                        await self.client.send_message(
                            sender.id,
                            "سلام! خریدارم. قیمت و جزییات؟"
                        )
                        self.sent_messages[seller_key] = datetime.now()
                        
                        # تأیید به مدیر
                        await self.client.send_message(
                            Config.ADMIN_USER_ID,
                            f"✅ به فروشنده پیام دادم (آی‌دی: {sender.id})"
                        )
                    except Exception as e:
                        logger.error(f"خطا در ارسال: {e}")

monitor = FoodMonitor()
