@client.on(events.NewMessage(chats=GROUP_ID))
async def message_handler(event):
    try:
        message_text = event.message.text or ''
        message_stats["total"] += 1
        
        if should_process_message(message_text):
            sender = await event.get_sender()
            
            # گرفتن آیدی کاربر
            username = f"@{sender.username}" if sender.username else "بدون آیدی"
            user_id = sender.id
            
            success = await send_quick_message(
                sender.id, 
                "سلام! غذا رو میخرم. لطفا قیمت و جزئیات رو بفرستید. ممنون"
            )
            
            if success:
                message_stats["success"] += 1
                # گزارش با آیدی کامل
                await send_report(
                    f"✅ پیام ارسال شد به:\n"
                    f"👤 نام: {sender.first_name or 'ناشناس'}\n"
                    f"🆔 آیدی: {username}\n"
                    f"🔢 عددی: {user_id}\n"
                    f"💬 پیام: {message_text[:50]}..."
                )
            else:
                await send_report(f"❌ خطا در ارسال به {username}")
            
    except Exception as e:
        print(f"خطا: {e}")
