"""
Telegram Email Cleanup Bot
Sends deletion proposals and handles user approvals
"""

import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime


class EmailCleanupBot:
    """Telegram bot for email cleanup approval workflow"""
    
    def __init__(self):
        """Initialize the bot"""
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file!")
        
        if not TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID not found in .env file!")
        
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = int(TELEGRAM_CHAT_ID)
        
        # Store current proposal for command handling
        self.current_proposal = None

        # Add deletion manager (will be set by bot_runner)
        self.deletion_manager = None
    
    def format_email_preview(self, email, index):
        """Format a single email for display"""
        subject = email.get('subject', 'No Subject')[:80]
        sender = email.get('from', {}).get('emailAddress', {})
        sender_name = sender.get('name', 'Unknown')
        sender_email = sender.get('address', 'Unknown')
        received = email.get('receivedDateTime', '')[:10]  # Just the date
        
        # Calculate age
        try:
            received_date = datetime.fromisoformat(received)
            age_days = (datetime.now() - received_date).days
            age_years = age_days // 365
            if age_years > 0:
                age_str = f"{age_years}+ years old"
            else:
                age_str = f"{age_days} days old"
        except:
            age_str = "Unknown age"
        
        return f"{index}. *{subject}*\n   From: {sender_name}\n   Age: {age_str}"
    
    def format_deletion_proposal(self, emails_to_delete, category_breakdown):
        """
        Format a deletion proposal message
        
        Args:
            emails_to_delete (list): List of email dicts to delete
            category_breakdown (dict): Count by category
            
        Returns:
            str: Formatted message for Telegram
        """
        total = len(emails_to_delete)
        
        message = f"🗑️ *DELETION PROPOSAL #{datetime.now().strftime('%Y%m%d_%H%M')}*\n\n"
        message += f"Found *{total} emails* safe to delete:\n\n"
        
        # Category breakdown
        if category_breakdown:
            message += "📊 *Breakdown:*\n"
            for category, count in category_breakdown.items():
                icon_map = {
                    'newsletter': '📰',
                    'promotional': '🛍️',
                    'informational': '📋',
                    'spam': '⚠️'
                }
                icon = icon_map.get(category, '📧')
                message += f"   {icon} {category.capitalize()}: {count}\n"
            message += "\n"
        
        # Show first 10 emails
        message += "📧 *Emails to delete:*\n"
        for i, email in enumerate(emails_to_delete[:10], 1):
            message += self.format_email_preview(email, i) + "\n"
        
        if total > 10:
            message += f"\n...and {total - 10} more\n"
        
        message += f"\n💾 *Total size:* ~{total * 0.05:.1f} MB\n"
        message += f"🎯 *Confidence:* High (all agents agree)\n\n"
        
        # Commands
        message += "\n\n💡 Reply with:\n"
        message += "✅ /yes - Delete all\n"
        message += "❌ /no - Keep all\n"
        message += "🎯 /delete_only 5,10 - Delete ONLY those (ranges: 1-5,10)\n"
        message += "🎯 /except 1,3,5 - Keep those, delete rest\n"
        message += "📄 /details - See full list"
        
        return message
    
    async def send_proposal(self, emails_to_delete, category_breakdown):
        """
        Send a deletion proposal to Telegram
        
        Args:
            emails_to_delete (list): Emails to propose for deletion
            category_breakdown (dict): Category counts
            
        Returns:
            bool: True if sent successfully
        """
        # Store proposal for later commands
        self.current_proposal = {
            'emails': emails_to_delete,
            'categories': category_breakdown,
            'timestamp': datetime.now()
        }
        
        message = self.format_deletion_proposal(emails_to_delete, category_breakdown)
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            return True
        except Exception as e:
            print(f"❌ Error sending proposal: {e}")
            return False
    
    async def send_confirmation(self, action, count, excluded=None):
        """
        Send confirmation message after action
        
        Args:
            action (str): 'approved', 'rejected', 'partial'
            count (int): Number of emails affected
            excluded (list): List of excluded indices (for partial)
        """
        if action == 'approved':
            message = f"✅ *DELETION APPROVED*\n\n"
            message += f"🗑️ Deleting {count} emails...\n"
            message += f"💾 Creating backup first...\n"
            message += f"⏳ This may take a moment..."
        
        elif action == 'rejected':
            message = f"❌ *DELETION CANCELLED*\n\n"
            message += f"🛡️ All {count} emails will be kept\n"
            message += f"✅ No changes made"
        
        elif action == 'partial':
            excluded_count = len(excluded) if excluded else 0
            delete_count = count - excluded_count
            message = f"🎯 *PARTIAL DELETION APPROVED*\n\n"
            message += f"🗑️ Deleting {delete_count} emails\n"
            message += f"🛡️ Keeping {excluded_count} emails\n"
            if excluded:
                message += f"📋 Excluded: {', '.join(map(str, excluded))}"
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            print(f"❌ Error sending confirmation: {e}")
    
    async def send_deletion_complete(self, deleted_count, errors=0, count_before=None, count_after=None, progress=None):
        """Send message when deletion is complete"""
        message = f"🎉 *DELETION COMPLETE!*\n\n"
        message += f"✅ Successfully deleted: {deleted_count} emails\n"
        
        if errors > 0:
            message += f"⚠️ Errors: {errors} emails\n"
        
            # NEW: Add inbox stats if available
        if count_before and count_after:
            message += f"\n📊 Inbox Status:\n"
            message += f"   Before: {count_before:,} emails\n"
            message += f"   After: {count_after:,} emails\n"
            if progress:
                message += f"   Progress: {progress:.2f}% cleaned\n"
        
        message += f"\n📊 Your inbox is now cleaner!\n"
        message += f"💾 Backup saved (can undo if needed)"
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            print(f"❌ Error sending completion message: {e}")
    
    async def send_error(self, error_message):
        """Send error message"""
        message = f"❌ *ERROR*\n\n{error_message}"
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            print(f"❌ Error sending error message: {e}")
    
    def parse_except_command(self, command_text):
        """
        Parse /except command to get excluded indices
        
        Args:
            command_text (str): e.g., "/except 1,3,5" or "/except 1 3 5"
            
        Returns:
            list: List of integers
        """
        try:
            # Remove /except and get the numbers
            numbers_part = command_text.replace('/except', '').strip()
            
            # Handle both comma and space separated
            if ',' in numbers_part:
                indices = [int(x.strip()) for x in numbers_part.split(',')]
            else:
                indices = [int(x.strip()) for x in numbers_part.split()]
            
            return indices
        except:
            return []
    
    def parse_number_range(self, text):
        """
        Parse numbers and ranges from command
        Examples: "1,5,10" or "1-5,10,15-20"
        Returns: list of integers
        """
        # Remove the command part
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return []
        
        number_text = parts[1]
        numbers = set()
        
        try:
            # Split by comma
            for part in number_text.split(','):
                part = part.strip()
                
                # Check if it's a range (e.g., "1-5")
                if '-' in part:
                    try:
                        start, end = part.split('-')
                        start = int(start.strip())
                        end = int(end.strip())
                        
                        # Add all numbers in range
                        numbers.update(range(start, end + 1))
                    except:
                        continue
                else:
                    # Single number
                    try:
                        numbers.add(int(part))
                    except:
                        continue
            
            return sorted(list(numbers))
        
        except Exception as e:
            print(f"❌ Error parsing numbers: {e}")
            return []
    
    async def handle_yes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /yes command - approve all deletions"""
        if not self.current_proposal:
            await update.message.reply_text("❌ No active proposal. Run /analyze first!")
            return
        
        emails = self.current_proposal['emails']
        count = len(emails)
        proposal_id = self.current_proposal['timestamp'].strftime('%Y%m%d_%H%M%S')
        
        # Send confirmation
        await self.send_confirmation('approved', count)
        
        # Check if deletion manager is available
        if not self.deletion_manager:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="⚠️ Deletion manager not initialized. Contact support."
            )
            return
        
        # REAL DELETION with backup
        try:
            results = self.deletion_manager.delete_emails(
                emails,
                proposal_id=proposal_id,
                create_backup=True
            )
            
            # Send completion message with real results
            await self.send_deletion_complete(
                deleted_count=results['success'],
                errors=results['failed'],
                count_before=results.get('count_before'),
                count_after=results.get('count_after'),
                progress=results.get('progress')
            )
            
            if results['failed'] > 0:
                error_msg = f"⚠️ {results['failed']} emails failed to delete:\n"
                for error in results['errors'][:5]:  # Show first 5 errors
                    error_msg += f"• {error['subject']}: {error['error']}\n"
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=error_msg
                )
            
        except Exception as e:
            await self.send_error(f"Deletion failed: {str(e)}")
        
        # Clear proposal
        self.current_proposal = None
    
    async def handle_no_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /no command - reject all deletions"""
        if not self.current_proposal:
            await update.message.reply_text("❌ No active proposal. Run analysis first!")
            return
        
        count = len(self.current_proposal['emails'])
        await self.send_confirmation('rejected', count)
        
        # Clear proposal
        self.current_proposal = None
    
    async def handle_delete_only_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delete_only command - delete ONLY specified indices"""
        if not self.current_proposal:
            await update.message.reply_text("❌ No active proposal. Run /analyze first!")
            return
        
        # Parse numbers (supports ranges like 1-5,10,15-20)
        indices_to_delete = self.parse_number_range(update.message.text)
        
        if not indices_to_delete:
            await update.message.reply_text(
                "❌ Invalid format!\n"
                "Examples:\n"
                "  /delete_only 5,10,15\n"
                "  /delete_only 1-5,10,15-20\n"
                "  /delete_only 1-30"
            )
            return
        
        # Filter emails to delete (ONLY specified indices)
        all_emails = self.current_proposal['emails']
        emails_to_delete = [email for i, email in enumerate(all_emails, 1) if i in indices_to_delete]
        emails_to_keep = [email for i, email in enumerate(all_emails, 1) if i not in indices_to_delete]
        
        if not emails_to_delete:
            await update.message.reply_text("❌ No valid email indices found!")
            return
        
        delete_count = len(emails_to_delete)
        keep_count = len(emails_to_keep)
        proposal_id = self.current_proposal['timestamp'].strftime('%Y%m%d_%H%M%S')
        
        # Send confirmation
        confirmation_msg = (
            f"🎯 DELETE ONLY SPECIFIED\n\n"
            f"🗑️ Deleting {delete_count} email(s): {', '.join(map(str, sorted(indices_to_delete)))}\n"
            f"🛡️ Keeping {keep_count} email(s)\n\n"
            f"💾 Creating backup first..."
        )
        await self.bot.send_message(chat_id=self.chat_id, text=confirmation_msg)
        
        # Check if deletion manager is available
        if not self.deletion_manager:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="⚠️ Deletion manager not initialized. Contact support."
            )
            return
        
        # REAL DELETION with backup
        try:
            results = self.deletion_manager.delete_emails(
                emails_to_delete,
                proposal_id=proposal_id,
                create_backup=True
            )
            
            # Send completion message with real results
            await self.send_deletion_complete(
                deleted_count=results['success'],
                errors=results['failed'],
                count_before=results.get('count_before'),
                count_after=results.get('count_after'),
                progress=results.get('progress')
            )
            
            if results['failed'] > 0:
                error_msg = f"⚠️ {results['failed']} emails failed to delete:\n"
                for error in results['errors'][:5]:
                    error_msg += f"• {error['subject']}: {error['error']}\n"
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=error_msg
                )
            
        except Exception as e:
            await self.send_error(f"Deletion failed: {str(e)}")
        
        # Clear proposal
        self.current_proposal = None

    async def handle_except_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /except command - delete all except specified indices"""
        if not self.current_proposal:
            await update.message.reply_text("❌ No active proposal. Run /analyze first!")
            return
        
        # Parse exception numbers
        excluded = self.parse_except_command(update.message.text)
        
        if not excluded:
            await update.message.reply_text("❌ Invalid format. Use: /except 1,3,5")
            return
        
        # Filter emails to delete (all except specified indices)
        all_emails = self.current_proposal['emails']
        emails_to_delete = [email for i, email in enumerate(all_emails, 1) if i not in excluded]
        emails_to_keep = [email for i, email in enumerate(all_emails, 1) if i in excluded]
        
        if not emails_to_delete:
            await update.message.reply_text("❌ No emails to delete! You excluded everything!")
            return
        
        delete_count = len(emails_to_delete)
        keep_count = len(emails_to_keep)
        proposal_id = self.current_proposal['timestamp'].strftime('%Y%m%d_%H%M%S')
        
        # Send partial approval confirmation
        await self.send_confirmation('partial', delete_count, excluded)
        
        # Check if deletion manager is available
        if not self.deletion_manager:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="⚠️ Deletion manager not initialized. Contact support."
            )
            return
        
        # REAL DELETION with backup
        try:
            results = self.deletion_manager.delete_emails(
                emails_to_delete,
                proposal_id=proposal_id,
                create_backup=True
            )
            
            # Send completion message with real results
            await self.send_deletion_complete(
                deleted_count=results['success'],
                errors=results['failed'],
                count_before=results.get('count_before'),
                count_after=results.get('count_after'),
                progress=results.get('progress')
            )
            
            if results['failed'] > 0:
                error_msg = f"⚠️ {results['failed']} emails failed to delete:\n"
                for error in results['errors'][:5]:
                    error_msg += f"• {error['subject']}: {error['error']}\n"
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=error_msg
                )
            
        except Exception as e:
            await self.send_error(f"Deletion failed: {str(e)}")
        
        # Clear proposal
        self.current_proposal = None
    
    async def handle_details_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /details command - show full list"""
        if not self.current_proposal:
            await update.message.reply_text("❌ No active proposal. Run analysis first!")
            return
        
        emails = self.current_proposal['emails']
        
        # Send in chunks of 20
        for i in range(0, len(emails), 20):
            chunk = emails[i:i+20]
            message = f"📧 *Emails {i+1}-{min(i+20, len(emails))}:*\n\n"
            
            for j, email in enumerate(chunk, i+1):
                message += self.format_email_preview(email, j) + "\n"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            
            await asyncio.sleep(1)  # Avoid rate limiting


# Test the bot
async def test_bot():
    """Test the Telegram bot with sample data"""
    print("="*100)
    print("🤖 TESTING TELEGRAM EMAIL CLEANUP BOT")
    print("="*100 + "\n")
    
    from datetime import timedelta
    
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
    
    # Initialize bot
    bot = EmailCleanupBot()

    # Initialize Outlook connector
    from core.outlook_connector import OutlookConnector
    print("🔐 Authenticating with Outlook...")
    outlook = OutlookConnector()
    if not outlook.authenticate():
        print("❌ Outlook authentication failed!")
        return

    # Create deletion manager and connect to bot
    from core.deletion_manager import DeletionManager
    deletion_manager = DeletionManager(outlook)
    bot.deletion_manager = deletion_manager  # ← Connect deletion manager to bot

    # Create Telegram application for command handling
    from telegram.ext import Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Store bot in application context so handlers can access it
    application.bot_data['cleanup_bot'] = bot
    
    # Send test proposal
    print("📤 Sending test deletion proposal to Telegram...")
    success = await bot.send_proposal(sample_emails, category_breakdown)
    
    if success:
        print("✅ Proposal sent successfully!")
        print("📱 Check your Telegram to see the proposal!")
        print("\n💡 Try the commands:")
        print("   /yes - Approve deletion")
        print("   /no - Reject deletion")
        print("   /except 1,2 - Delete all except 1 and 2")
        print("   /details - See full list")
    else:
        print("❌ Failed to send proposal")


if __name__ == "__main__":
    asyncio.run(test_bot())