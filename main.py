# main.py
import asyncio
from userbot.monitor import monitor
from shared.config import validate_config
import sys

async def main():
    print("🚀 شروع ربات خرید غذا...")
    
    if not validate_config():
        print("❌ تنظیمات نادرست")
        sys.exit(1)
    
    await monitor.start()

if __name__ == "__main__":
    asyncio.run(main())
