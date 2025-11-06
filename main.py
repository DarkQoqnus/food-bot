from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

API_ID = 28175931
API_HASH = '2455aeda9d813346dd8e12d06c331e12'
PHONE = '+989156707283'

async def main():
    # استفاده از StringSession بجای فایل
    session = StringSession()
    client = TelegramClient(session, API_ID, API_HASH)
    
    await client.start(PHONE)
    
    # گرفتن session string
    session_string = client.session.save()
    
    print("\n" + "="*50)
    print("SESSION_STRING شما:")
    print(session_string)
    print("="*50)
    
    # تست اتصال
    me = await client.get_me()
    print(f"\n✅ وصل شد به: {me.first_name}")
    
    await client.disconnect()

asyncio.run(main())
