counter['minute_count'] = counter.get('minute_count', 0) + 1
        counter['hour_count'] = counter.get('hour_count', 0) + 1
    
    def should_process_message(self, message_text):
        """بررسی اینکه پیام باید پردازش شود یا نه"""
        if self.current_filter == "همه":
            return any(keyword in message_text for keyword in LOCATION_FILTERS["همه"])
        else:
            filter_keywords = LOCATION_FILTERS.get(self.current_filter, [])
            return any(keyword in message_text for keyword in filter_keywords)
    
    async def setup_handlers(self):
        """تنظیم هندلر برای تمام کلاینت‌ها"""
        for i, client in enumerate(self.clients):
            @client.on(events.NewMessage(chats=GROUP_ID))
            async def handler(event):
                if self.is_paused:
                    return
                    
                try:
                    message = event.message
                    message_text = message.text or ''
                    sender = await event.get_sender()
                    
                    if self.should_process_message(message_text):
                        self.logger.info(f"پیام تشخیص داده شد از {sender.first_name}: {message_text[:50]}...")
                        
                        report = f"""
🔔 <b>پیام جدید تشخیص داده شد</b>

👤 <b>فرستنده:</b> {sender.first_name or 'ناشناس'}
💬 <b>پیام:</b> {message_text[:100]}...
🏢 <b>فیلتر:</b> {self.current_filter}
⏰ <b>زمان:</b> {datetime.now().strftime('%H:%M')}

📊 <i>وضعیت: تشخیص داده شد - آماده ارسال پیام</i>
"""
                        await self.send_bot_message(report)
                        
                except Exception as e:
                    self.logger.error(f"خطا در پردازش پیام: {e}")
                    await self.send_bot_message(f"❌ خطا در پردازش: {e}")
    
    async def run(self):
        """اجرای اصلی"""
        await self.send_bot_message("🤖 <b>ربات فروش غذا شروع به کار کرد</b>")
        await self.initialize_accounts()
        await self.setup_handlers()
        
        self.logger.info("✅ ربات شروع به کار کرد و در حال مانیتورینگ...")
        
        # نگه‌داری کلاینت‌ها
        await asyncio.gather(*[client.run_until_disconnected() for client in self.clients])

# اجرای ربات
async def main():
    bot_manager = FoodBotManager()
    await bot_manager.run()

if name == '__main__':
    asyncio.run(main())
