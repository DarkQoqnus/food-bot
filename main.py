# main.py
import asyncio
import logging
from userbot.monitor import monitor
from shared.config import validate_config
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print("=" * 50)
    print("🚀 شروع ربات خرید غذا...")
    print("=" * 50)
    
    # اعتبارسنجی تنظیمات
    if not validate_config():
        print("❌ خطا در تنظیمات")
        sys.exit(1)
    
    print("✅ تنظیمات OK. شروع ربات...")
    
    # شروع ربات
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
