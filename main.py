"""
Email Cleanup Agent - Main Integration
Connects Outlook with Document Preservation Agent
"""

from core.outlook_connector import OutlookConnector
from agents.document_preservation_agent import DocumentPreservationAgent

def test_agent_on_real_emails():
    """Test the Document Preservation Agent on real emails"""
    
    print("="*100)
    print("🚀 EMAIL CLEANUP AGENT - Real Email Analysis")
    print("="*100 + "\n")
    
    # Initialize components
    print("📧 Connecting to Outlook...")
    connector = OutlookConnector()
    
    if not connector.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("\n🤖 Initializing Document Preservation Agent...")
    agent = DocumentPreservationAgent()
    
    if agent.vip_emails:
        print(f"🔒 VIP Protection: {len(agent.vip_emails)} email(s)")
    
    # Get inbox stats
    print("\n" + "="*100)
    stats = connector.get_inbox_stats()
    
    # Test on Focused inbox (important emails)
    print("\n" + "="*100)
    print("🎯 TESTING ON FOCUSED INBOX (Important Emails)")
    print("="*100)
    
    focused_emails = connector.get_emails(limit=20, inbox_type='focused')
    
    if focused_emails:
        results = agent.batch_analyze(focused_emails)
        
        print("\n" + "="*100)
        print("📊 FOCUSED INBOX RESULTS")
        print("="*100)
        print(f"✅ To Preserve: {len(results['preserve'])}")
        print(f"⚠️ Uncertain: {len(results['uncertain'])}")
        print(f"❌ Safe to Delete: {len(results['safe_to_delete'])}")
        
        # Show preserve breakdown
        if results['preserve']:
            print(f"\n🛡️ Preserved by method:")
            methods = {}
            for item in results['preserve']:
                method = item['analysis']['method']
                methods[method] = methods.get(method, 0) + 1
            for method, count in methods.items():
                print(f"   {method}: {count}")
    
    print("\n" + "="*100)
    print("✅ Analysis Complete!")
    print("="*100 + "\n")

if __name__ == "__main__":
    test_agent_on_real_emails()