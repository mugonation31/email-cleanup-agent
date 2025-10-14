"""
Test sending a message via Telegram bot
"""

import asyncio
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def send_test_message():
    """Send a test message to verify bot works"""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env!")
        return
    
    if not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_CHAT_ID not found in .env!")
        return
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    print("🤖 Sending test message...")
    
    try:
        message = """
🎉 *Email Cleanup Bot is Online!*

✅ Connection successful
🤖 Your bot is ready to send deletion proposals
📱 You'll receive notifications here

Ready for Week 4! 🚀
"""
        
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        
        print("✅ Message sent successfully!")
        print("📱 Check your Telegram - you should see the test message!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())