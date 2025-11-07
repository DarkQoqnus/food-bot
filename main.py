print("🚀 Starting Food Bot...")

try:
    # اول فقط ربات مدیریت رو اجرا کن
    from bot_manager_simple import start_bot
    print("🤖 Starting Bot Manager...")
    start_bot()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
