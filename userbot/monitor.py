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
        self.bad_words = []  # کلمات فیلتر منفی
        self.found_items = []  # لیست غذاهای پیدا شده
        self.sent_messages = {}  # پیام‌های ارسال شده
        self.start_time = datetime.now()
    
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
                    f"🕒 زمان شروع: {self.start_time.strftime('%Y/%m/%d %H:%M:%S')}\n"
                    f"👤 اکانت: @{me.username}\n\n"
                    f"📝 دستورات:\n"
                    f"• روشن - شروع نظارت\n"
                    f"• خاموش - توقف نظارت\n"
                    f"• سلف/حافظ - تغییر فیلتر\n"
                    f"• وضعیت - نمایش وضعیت\n"
                    f"• لیست - آخرین یافته‌ها\n"
                    f"• حذف فیلتر [کلمه] - حذف کلمه از فیلتر"
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
                    
                elif "حذف فیلتر" in message:
                    # حذف کلمات خاص از فیلتر منفی
                    words_to_remove = message.replace("حذف فیلتر", "").strip().split()
                    removed = []
                    for word in words_to_remove:
                        if word in self.bad_words:
                            self.bad_words.remove(word)
                            removed.append(word)
                    
                    if removed:
                        await event.reply(f"✅ کلمات حذف شدند: {', '.join(removed)}")
                    else:
                        await event.reply(f"⚠️ هیچکدام از کلمات در لیست فیلتر نیستند")
                    
                elif message == "لیست":
                    # نمایش آخرین یافته‌ها
                    if not self.found_items:
                        await event.reply("📭 هنوز غذایی پیدا نشده است.")
                    else:
                        # نمایش ۵ آیتم آخر
                        recent = self.found_items[-5:]  # ۵ تا آخر
                        response = "📊 **آخرین یافته‌ها:**\n\n"
                        
                        for i, item in enumerate(recent[::-1], 1):  # معکوس برای نمایش جدید به قدیم
                            time_str = item['time'].strftime('%H:%M')
                            response += f"{i}. ⏰ {time_str} | 🔍 {item['filter']}\n"
                            response += f"   📝 {item['text'][:80]}...\n"
                            response += f"   👤 {item['seller']}\n\n"
                        
                        response += f"📈 مجموع: {len(self.found_items)} غذا"
                        await event.reply(response)
                    
                elif message == "وضعیت":
                    status = "فعال ✅" if self.is_monitoring else "غیرفعال ❌"
                    uptime = datetime.now() - self.start_time
                    hours, remainder = divmod(uptime.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    await event.reply(
                        f"📊 **وضعیت ربات:**\n\n"
                        f"• 🔍 نظارت: {status}\n"
                        f"• 🏷️ فیلتر فعلی: {self.current_filter}\n"
                        f"• 📊 کل یافته‌ها: {len(self.found_items)}\n"
                        f"• ⏰ زمان کار: {hours}h {minutes}m {seconds}s\n"
                        f"• 🎯 گروه هدف: {Config.TARGET_GROUP_ID}\n"
                        f"• 🚫 فیلترهای منفی: {len(self.bad_words)} کلمه\n"
                        f"• 🕒 آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    
                else:
                    await event.reply(
                        "🤖 **دستورات ربات:**\n\n"
                        "🟢 **کنترل:**\n"
                        "• روشن - شروع نظارت\n"
                        "• خاموش - توقف نظارت\n\n"
                        "🔍 **فیلتر:**\n"
                        "• سلف - جستجوی غذاهای سلف\n"
                        "• حافظ - جستجوی غذاهای حافظ\n\n"
                        "📊 **اطلاعات:**\n"
                        "• وضعیت - نمایش وضعیت\n"
                        "• لیست - آخرین یافته‌ها\n\n"
                        "⚙️ **تنظیمات:**\n"
                        "• حذف فیلتر [کلمه] - حذف کلمه"
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
                
                # بررسی فیلتر منفی (اگر کلمه ناخواسته بود، نادیده بگیر)
                if any(bad_word in message_text for bad_word in self.bad_words):
                    logger.info(f"⏭️ پیام رد شد (حاوی کلمه فیلتر شده)")
                    return
                
                # بررسی فیلتر اصلی
                if self.current_filter in message_text:
                    # ذخیره در تاریخچه
                    self.found_items.append({
                        'time': datetime.now(),
                        'text': message_text[:200],
                        'seller': sender.id,
                        'filter': self.current_filter,
                        'seller_name': sender.first_name
                    })
                    
                    # حفظ فقط ۱۰۰ آیتم آخر
                    if len(self.found_items) > 100:
                        self.found_items = self.found_items[-100:]
                    
                    # چاپ در لاگ Railway
                    logger.info(f"\n{'='*50}")
                    logger.info(f"🚨 غذای {self.current_filter} پیدا شد!")
                    logger.info(f"📝 پیام: {message_text[:100]}")
                    logger.info(f"👤 فروشنده: {sender.id} ({sender.first_name})")
                    logger.info(f"{'='*50}\n")
                    
                    # گزارش به مدیر
                    await self.client.send_message(
                        Config.ADMIN_USER_ID,
                        f"🔔 **غذا پیدا شد!**\n\n"
                        f"🏷️ نوع: {self.current_filter}\n"
                        f"📝 متن: {message_text[:150]}...\n"
                        f"👤 فروشنده: {sender.first_name}\n"
                        f"🆔 آی‌دی: {sender.id}\n"
                        f"⏰ زمان: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    
                    # ارسال پیام به فروشنده
                    try:
                        # بررسی نکرده باشیم قبلاً به این فروشنده پیام داده‌ایم
                        seller_key = f"{sender.id}_{self.current_filter}"
                        if seller_key not in self.sent_messages:
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
                            self.sent_messages[seller_key] = datetime.now()
                            
                            # تأیید به مدیر
                            await self.client.send_message(
                                Config.ADMIN_USER_ID,
                                f"✅ پیام خرید ارسال شد:\n"
                                f"👤 به: {sender.first_name}\n"
                                f"🆔 آی‌دی: {sender.id}\n"
                                f"🏷️ نوع: {self.current_filter}"
                            )
                        else:
                            logger.info(f"⚠️ قبلاً به {sender.id} پیام داده شده")
                            
                    except Exception as e:
                        logger.error(f"خطا در ارسال به فروشنده: {e}")
                        await self.client.send_message(
                            Config.ADMIN_USER_ID,
                            f"❌ خطا در ارسال پیام:\n{str(e)[:200]}"
                        )
                        
            except Exception as e:
                logger.error(f"خطا در پردازش پیام گروه: {e}")

monitor = FoodMonitor()
