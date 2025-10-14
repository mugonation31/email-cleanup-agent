"""
Quick script to get your Telegram Chat ID
Run this once to find your chat ID
"""

import asyncio
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN

async def get_chat_id():
    """Get the chat ID from recent updates"""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file!")
        return
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    print("🤖 Fetching recent messages...")
    print("📱 Make sure you've sent a message to your bot on Telegram!")
    print()
    
    try:
        updates = await bot.get_updates()
        
        if not updates:
            print("❌ No messages found!")
            print("👉 Open Telegram and send a message to your bot, then run this again.")
            return
        
        print(f"✅ Found {len(updates)} message(s)!\n")
        
        # Get unique chat IDs
        chat_ids = set()
        for update in updates:
            if update.message:
                chat_id = update.message.chat.id
                chat_ids.add(chat_id)
                print(f"📱 Chat ID: {chat_id}")
                print(f"   From: {update.message.from_user.first_name}")
                print(f"   Message: {update.message.text}")
                print()
        
        if chat_ids:
            print("=" * 60)
            print("🎯 ADD THIS TO YOUR .env FILE:")
            print("=" * 60)
            # Use the first chat ID found
            print(f"TELEGRAM_CHAT_ID={list(chat_ids)[0]}")
            print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure your bot token is correct!")

if __name__ == "__main__":
    asyncio.run(get_chat_id())