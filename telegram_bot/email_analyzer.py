"""
Email Analyzer for Telegram Bot
Connects multi-agent system to Telegram bot for real email analysis
"""

import asyncio
from core.outlook_connector import OutlookConnector
from core.multi_agent_orchestrator import MultiAgentOrchestrator
from telegram_bot.email_cleanup_bot import EmailCleanupBot


class EmailAnalyzer:
    """Analyzes real emails and sends proposals to Telegram"""
    
    def __init__(self):
        """Initialize analyzer with all components"""
        print("🔧 Initializing Email Analyzer...")
        
        self.outlook = OutlookConnector()
        self.orchestrator = MultiAgentOrchestrator()
        self.telegram_bot = EmailCleanupBot()
        
        print("✅ Email Analyzer ready!")
    
    def authenticate(self):
        """Authenticate with Outlook"""
        return self.outlook.authenticate()
    
    async def analyze_and_propose(self, limit=50, inbox_type='other'):
        """
        Analyze emails and send deletion proposal to Telegram
        
        Args:
            limit (int): Number of emails to analyze
            inbox_type (str): 'focused' or 'other'
            
        Returns:
            dict: Analysis results
        """
        print(f"\n📧 Fetching {limit} emails from {inbox_type.upper()} inbox...")
        
        # Fetch emails
        emails = self.outlook.get_emails(limit=limit, inbox_type=inbox_type)
        
        if not emails:
            await self.telegram_bot.send_error("❌ No emails fetched from inbox!")
            return None
        
        print(f"✅ Fetched {len(emails)} emails")
        print(f"\n🤖 Running multi-agent analysis...")
        
        # Run multi-agent analysis
        results = self.orchestrator.batch_analyze(emails)
        
        # Extract deletion candidates
        delete_emails = [item['email'] for item in results['delete']]
        preserve_emails = results['preserve']
        review_emails = results['review']
        
        print(f"\n📊 Analysis Results:")
        print(f"   🗑️ Safe to delete: {len(delete_emails)}")
        print(f"   🛡️ Preserve: {len(preserve_emails)}")
        print(f"   👁️ Review needed: {len(review_emails)}")
        
        if not delete_emails:
            await self.telegram_bot.send_error(
                "✅ No emails found that are safe to delete!\n\n"
                "All analyzed emails are either:\n"
                "• Important documents\n"
                "• Personal emails\n"
                "• Need human review"
            )
            return {
                'delete': [],
                'preserve': preserve_emails,
                'review': review_emails
            }
        
        # Build category breakdown
        category_breakdown = {}
        for item in results['delete']:
            category = item['analysis']['classification']['category']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        print(f"\n📤 Sending deletion proposal to Telegram...")
        
        # Send proposal to Telegram
        success = await self.telegram_bot.send_proposal(delete_emails, category_breakdown)
        
        if success:
            print(f"✅ Proposal sent successfully!")
            print(f"📱 Check your Telegram to approve/reject!")
        else:
            print(f"❌ Failed to send proposal")
        
        return {
            'delete': delete_emails,
            'preserve': preserve_emails,
            'review': review_emails,
            'category_breakdown': category_breakdown
        }
    
    async def analyze_batch(self, batch_size=50, max_batches=5):
        """
        Analyze multiple batches of emails
        
        Args:
            batch_size (int): Emails per batch
            max_batches (int): Maximum number of batches
        """
        total_analyzed = 0
        total_deletable = 0
        
        for batch_num in range(1, max_batches + 1):
            print(f"\n{'='*100}")
            print(f"📦 BATCH {batch_num}/{max_batches}")
            print(f"{'='*100}")
            
            results = await self.analyze_and_propose(limit=batch_size)
            
            if results:
                total_analyzed += batch_size
                total_deletable += len(results['delete'])
                
                if results['delete']:
                    # Wait for user to respond before next batch
                    print(f"\n⏸️ Waiting for your response in Telegram before next batch...")
                    print(f"💡 Respond with /yes, /no, or /except, then I'll continue")
                    
                    # In a real implementation, we'd wait for the user's response
                    # For now, we'll just pause
                    break
            else:
                break
        
        print(f"\n{'='*100}")
        print(f"📊 BATCH ANALYSIS COMPLETE")
        print(f"{'='*100}")
        print(f"   Total analyzed: {total_analyzed} emails")
        print(f"   Total deletable: {total_deletable} emails")
        print(f"{'='*100}\n")


async def run_analysis():
    """Run a complete email analysis"""
    print("="*100)
    print("📧 REAL EMAIL ANALYSIS WITH TELEGRAM PROPOSALS")
    print("="*100 + "\n")
    
    analyzer = EmailAnalyzer()
    
    # Authenticate
    print("🔐 Authenticating with Outlook...")
    if not analyzer.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("✅ Authentication successful!\n")
    
    # Analyze emails
    await analyzer.analyze_and_propose(limit=10, inbox_type='other')


if __name__ == "__main__":
    asyncio.run(run_analysis())