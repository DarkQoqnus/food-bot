import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # کنترل‌بات
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # یوزربات
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    
    # گروه هدف
    TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", 0))
    
    # مدیر
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))
    
    # وضعیت
    IS_MONITORING = False
    CURRENT_FILTER = "سلف"
    
    # دیتابیس
    REDIS_URL = os.getenv("REDIS_URL", "")
    MONGODB_URI = os.getenv("MONGODB_URI", "")
