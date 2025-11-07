import os

# تنظیمات اصلی
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
YOUR_USER_ID = int(os.environ['YOUR_USER_ID'])
SESSION_STRING = os.environ['SESSION_STRING']
GROUP_ID = int(os.environ['GROUP_ID'])

# وضعیت ربات
bot_status = "on"
current_filter = "همه"
message_stats = {"total": 0, "success": 0}

# کلمات کلیدی
LOCATION_FILTERS = {
    "سلف": ["سلف", "سلفی", "غذای سلف", "سلف دانشگاه", "مرکزی"],
    "حافظ": ["حافظ", "حافظی", "غذای حافظ"],
    "همه": ["فروش", "میفروشم", "فروشی"]
}
