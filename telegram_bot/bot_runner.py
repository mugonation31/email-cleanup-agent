"""
Telegram Bot Runner
Keeps the bot running and listening for commands
"""

from telegram.ext import Application, CommandHandler
from telegram_bot.email_cleanup_bot import EmailCleanupBot
from config.settings import TELEGRAM_BOT_TOKEN
from core.multi_agent_orchestrator import MultiAgentOrchestrator


async def start_command(update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Welcome to Email Cleanup Bot!\n\n"
        "I'll help you safely delete old unwanted emails.\n\n"
        "Commands:\n"
        "/yes - Approve deletion\n"
        "/no - Reject deletion\n"
        "/except N,N,N - Delete all except those\n"
        "/details - See full list\n"
        "/help - Show this message"
    )


async def help_command(update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "🤖 *Email Cleanup Bot Commands:*\n\n"
        "✅ `/yes` - Approve all deletions\n"
        "❌ `/no` - Reject all deletions\n"
        "🎯 `/except 1,3,5` - Delete all except those numbers\n"
        "📄 `/details` - Show full email list\n"
        "❓ `/help` - Show this message\n\n"
        "💡 The bot will send you deletion proposals.\n"
        "Review them and respond with a command!",
        parse_mode='Markdown'
    )

async def test_command(update, context):
    """Handle /test command - send a test proposal"""
    from datetime import datetime, timedelta
    
    # Get the bot instance from context
    bot = context.application.bot_data['cleanup_bot']
    
    # Create sample emails
    today = datetime.now()
    sample_emails = [
        {
            'subject': 'Job Alert: Senior Developer',
            'from': {'emailAddress': {'address': 'alerts@indeed.com', 'name': 'Indeed'}},
            'receivedDateTime': (today - timedelta(days=800)).isoformat(),
        },
        {
            'subject': 'Weekly Newsletter - Tech Updates',
            'from': {'emailAddress': {'address': 'news@techcrunch.com', 'name': 'TechCrunch'}},
            'receivedDateTime': (today - timedelta(days=1000)).isoformat(),
        },
        {
            'subject': 'FLASH SALE - 70% OFF',
            'from': {'emailAddress': {'address': 'deals@store.com', 'name': 'Store'}},
            'receivedDateTime': (today - timedelta(days=500)).isoformat(),
        },
    ]
    
    category_breakdown = {
        'newsletter': 2,
        'promotional': 1
    }
    
    # Send proposal
    await bot.send_proposal(sample_emails, category_breakdown)
    await update.message.reply_text("✅ Test proposal sent! Try the commands now.")

async def analyze_command(update, context):
    """Handle /analyze command - run real email analysis"""
    from core.outlook_connector import OutlookConnector
    
    await update.message.reply_text("🔄 Starting email analysis...\nThis may take a minute!")
    
    # Get the bot instance from context
    bot = context.application.bot_data['cleanup_bot']
    
    # Get orchestrator
    orchestrator = context.application.bot_data['orchestrator']
    outlook = context.application.bot_data['outlook']
    
    # Fetch emails
    try:
        emails = outlook.get_emails(limit=100, inbox_type='other')
        
        if not emails:
            await update.message.reply_text("❌ No emails fetched!")
            return
        
        await update.message.reply_text(f"✅ Fetched {len(emails)} emails\n🤖 Running analysis...")
        
        # Run multi-agent analysis
        results = orchestrator.batch_analyze(emails)
        
        # Extract deletion candidates
        delete_emails = [item['email'] for item in results['delete']]
        
        if not delete_emails:
            await update.message.reply_text(
                "✅ No emails found safe to delete!\n"
                "All emails are either important or need review."
            )
            return
        
        # Build category breakdown
        category_breakdown = {}
        for item in results['delete']:
            category = item['analysis']['classification']['category']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        # Send proposal using the SAME bot instance
        await bot.send_proposal(delete_emails, category_breakdown)
        await update.message.reply_text("✅ Proposal sent! Use /yes, /no, /delete_only, /except, or /details")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Run the bot"""
    print("="*100)
    print("🤖 STARTING EMAIL CLEANUP BOT")
    print("="*100 + "\n")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found!")
        return
    
    # Initialize components ONCE
    from core.outlook_connector import OutlookConnector
    
    print("🔐 Authenticating with Outlook...")
    outlook = OutlookConnector()
    if not outlook.authenticate():
        print("❌ Outlook authentication failed!")
        return
    
    print("🤖 Initializing orchestrator...")
    orchestrator = MultiAgentOrchestrator()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Create bot instance (shared across handlers)
    bot = EmailCleanupBot()

    # Create deletion manager and connect to bot 
    from core.deletion_manager import DeletionManager 
    deletion_manager = DeletionManager(outlook)  
    bot.deletion_manager = deletion_manager  
        
    # Store bot in application context so handlers can access it
    application.bot_data['cleanup_bot'] = bot
    application.bot_data['orchestrator'] = orchestrator
    application.bot_data['outlook'] = outlook 
    
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("yes", bot.handle_yes_command))
    application.add_handler(CommandHandler("no", bot.handle_no_command))
    application.add_handler(CommandHandler("delete_only", bot.handle_delete_only_command))
    application.add_handler(CommandHandler("except", bot.handle_except_command))
    application.add_handler(CommandHandler("details", bot.handle_details_command))
    application.add_handler(CommandHandler("analyze", analyze_command)) 
    
    print("✅ Bot initialized!")
    print("📱 Listening for commands...")
    print("💡 Press Ctrl+C to stop\n")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    from telegram import Update
    main()