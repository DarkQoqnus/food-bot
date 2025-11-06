from telethon import TelegramClient
import asyncio

API_ID = 28175931
API_HASH = '2455aeda9d813346dd8e12d06c331e12'
PHONE_NUMBER = '+989156707283'

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(PHONE_NUMBER)
    
    session_string = client.session.save()
    print("\n" + "="*50)
    print("SESSION_STRING شما:")
    print(session_string)
    print("="*50)
    
    await client.disconnect()

asyncio.run(main())
