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
    
    # Test on Other inbox (important emails)
    print("\n" + "="*100)
    print("🎯 TESTING ON OTHER INBOX (Important Emails)")
    print("="*100)
    
    other_emails = connector.get_emails(limit=20, inbox_type='other')
    
    if other_emails:
        results = agent.batch_analyze(other_emails)
        
        print("\n" + "="*100)
        print("📊 OTHER INBOX RESULTS")
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

    if stats:
        print(f"\n💡 Your inbox has {stats['focused']:,} important emails and {stats['other']:,} other emails")
        print(f"   That's a {(stats['other']/stats['total']*100):.1f}% spam/newsletter rate!")


def test_classifier_on_real_emails():
    """Test the Classifier Agent on real emails"""
    
    print("="*100)
    print("🏷️ EMAIL CLASSIFIER - Real Email Analysis")
    print("="*100 + "\n")
    
    # Initialize components
    print("📧 Connecting to Outlook...")
    connector = OutlookConnector()
    
    if not connector.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("\n🤖 Initializing Classifier Agent...")
    from agents.classifier_agent import ClassifierAgent
    agent = ClassifierAgent()
    
    # Get inbox stats
    print("\n" + "="*100)
    stats = connector.get_inbox_stats()
    
    # Test on Other inbox (where classification matters most)
    print("\n" + "="*100)
    print("🎯 TESTING CLASSIFIER ON OTHER INBOX")
    print("="*100)
    
    other_emails = connector.get_emails(limit=30, inbox_type='other')
    
    if other_emails:
        results = agent.batch_classify(other_emails)
        
        print("\n" + "="*100)
        print("📊 CLASSIFICATION RESULTS")
        print("="*100)
        
        for category in ['urgent', 'personal', 'newsletter', 'promotional', 'informational', 'spam']:
            count = len(results[category])
            if count > 0:
                percentage = (count / len(other_emails)) * 100
                icon = {'urgent': '🚨', 'personal': '📧', 'newsletter': '📰', 
                       'promotional': '🛍️', 'informational': '📋', 'spam': '⚠️'}[category]
                print(f"{icon} {category.upper()}: {count} ({percentage:.1f}%)")
        
        print("="*100)
    
    print("\n✅ Classification Complete!\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'classify':
        test_classifier_on_real_emails()
    else:
        test_agent_on_real_emails()