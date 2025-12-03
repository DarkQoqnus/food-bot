# shared/config.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    # کنترل‌بات
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # یوزربات
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    
    # گروه هدف
    TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", 0))
    
    # مدیر
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))
    
    # تنظیمات نظارت
    IS_MONITORING = False
    CURRENT_FILTER = "سلف"
    
    # دیتابیس
    REDIS_URL = os.getenv("REDIS_URL", "")
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    
    # تنظیمات Railway
    SKIP_PENDING = os.getenv("SKIP_PENDING", "True").lower() == "true"
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))

def validate_config():
    """اعتبارسنجی تنظیمات و نمایش اطلاعات"""
    errors = []
    
    # بررسی BOT_TOKEN
    if not Config.BOT_TOKEN:
        errors.append("❌ BOT_TOKEN تنظیم نشده است")
    elif ":" not in Config.BOT_TOKEN:
        errors.append("❌ فرمت BOT_TOKEN نامعتبر است (فرمت صحیح: 123456:ABCdef...)")
    
    # بررسی API_ID
    if Config.API_ID <= 0:
        errors.append("❌ API_ID نامعتبر یا تنظیم نشده است")
    
    # بررسی API_HASH
    if not Config.API_HASH:
        errors.append("❌ API_HASH تنظیم نشده است")
    elif len(Config.API_HASH) < 10:
        errors.append("❌ طول API_HASH بسیار کوتاه است")
    
    # بررسی SESSION_STRING
    if not Config.SESSION_STRING:
        errors.append("⚠️ SESSION_STRING تنظیم نشده - با ربات کار خواهد کرد اما یوزربات ممکن است مشکل داشته باشد")
    
    # بررسی ADMIN_USER_ID
    if Config.ADMIN_USER_ID <= 0:
        errors.append("❌ ADMIN_USER_ID نامعتبر یا تنظیم نشده است")
    
    # بررسی TARGET_GROUP_ID
    if Config.TARGET_GROUP_ID >= 0:
        errors.append("❌ TARGET_GROUP_ID باید عددی منفی باشد (ایدی گروهها منفی است)")
    
    # نمایش خطاها
    if errors:
        print("\n" + "="*60)
        print("🚨 خطاهای پیکربندی:")
        for error in errors:
            print(f"   {error}")
        print("="*60)
        
        # راهنمایی برای رفع خطاها
        if "BOT_TOKEN" in errors[0]:
            print("\n📝 راهنمایی:")
            print("   BOT_TOKEN را از @BotFather دریافت کنید")
            print("   دستور: /newbot (یا از ربات موجود /mybots → API Token)")
        
        if "API_ID" in errors[1]:
            print("\n📝 راهنمایی:")
            print("   API_ID و API_HASH را از سایت زیر دریافت کنید:")
            print("   https://my.telegram.org/auth")
            print("   به بخش 'API development tools' بروید")
        
        if "SESSION_STRING" in errors[2]:
            print("\n📝 راهنمایی:")
            print("   برای تولید SESSION_STRING از اسکریپت generate_session.py استفاده کنید")
        
        if "TARGET_GROUP_ID" in errors[3]:
            print("\n📝 راهنمایی:")
            print("   آی‌دی گروه را با ربات @username_to_id_bot دریافت کنید")
            print("   آی‌دی گروهها معمولاً منفی هستند (مثال: -1001234567890)")
        
        return False
    
    # نمایش اطلاعات پیکربندی (بدون اطلاعات حساس کامل)
    print("\n" + "="*60)
    print("📋 اطلاعات پیکربندی:")
    print("="*60)
    
    # نمایش BOT_TOKEN به صورت مخفی
    if Config.BOT_TOKEN:
        token_parts = Config.BOT_TOKEN.split(":")
        if len(token_parts) >= 2:
            masked_token = f"{token_parts[0]}:{'*' * 10}{token_parts[1][-4:] if len(token_parts[1]) > 4 else '****'}"
            print(f"   🤖 BOT_TOKEN: {masked_token}")
    
    # نمایش API_ID
    print(f"   🔑 API_ID: {Config.API_ID}")
    
    # نمایش API_HASH به صورت مخفی
    if Config.API_HASH:
        masked_hash = Config.API_HASH[:4] + "*" * 10 + Config.API_HASH[-4:] if len(Config.API_HASH) > 8 else "****"
        print(f"   🔐 API_HASH: {masked_hash}")
    
    # نمایش SESSION_STRING
    if Config.SESSION_STRING:
        session_status = "✅ تنظیم شده"
        if len(Config.SESSION_STRING) < 100:
            session_status = "⚠️ کوتاه (ممکن است مشکل داشته باشد)"
        print(f"   🔗 SESSION_STRING: {session_status}")
    else:
        print(f"   🔗 SESSION_STRING: ❌ تنظیم نشده")
    
    # نمایش سایر اطلاعات
    print(f"   👤 ADMIN_USER_ID: {Config.ADMIN_USER_ID}")
    print(f"   📢 TARGET_GROUP_ID: {Config.TARGET_GROUP_ID}")
    print(f"   🔍 CURRENT_FILTER: {Config.CURRENT_FILTER}")
    print(f"   ⚙️ SKIP_PENDING: {Config.SKIP_PENDING}")
    print(f"   🔄 MAX_RETRIES: {Config.MAX_RETRIES}")
    
    # بررسی تنظیمات اضافی
    print("\n🔍 بررسی اضافی:")
    
    # بررسی دیتابیس
    if Config.REDIS_URL:
        print(f"   🗄️ Redis: ✅ تنظیم شده")
    else:
        print(f"   🗄️ Redis: ⚠️ تنظیم نشده (استفاده از حافظه موقت)")
    
    if Config.MONGODB_URI:
        print(f"   🗄️ MongoDB: ✅ تنظیم شده")
    else:
        print(f"   🗄️ MongoDB: ⚠️ تنظیم نشده")
    
    print("="*60)
    print("✅ تنظیمات اعتبارسنجی شد")
    print("="*60)
    
    return True

# تست در صورت اجرای مستقیم
if __name__ == "__main__":
    print("🔧 تست پیکربندی...")
    if validate_config():
        print("\n✅ همه چیز برای شروع آماده است!")
    else:
        print("\n❌ لطفاً خطاهای بالا را رفع کنید")
        sys.exit(1)
