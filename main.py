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

def test_all_agents_on_real_emails():
        """Test all three agents working together on real emails"""
    
        print("="*100)
        print("🤖 ALL AGENTS WORKING TOGETHER - Real Email Analysis")
        print("="*100 + "\n")
        
        # Initialize components
        print("📧 Connecting to Outlook...")
        connector = OutlookConnector()
        
        if not connector.authenticate():
            print("❌ Authentication failed!")
            return
        
        print("\n🤖 Initializing All Agents...")
        from agents.document_preservation_agent import DocumentPreservationAgent
        from agents.classifier_agent import ClassifierAgent
        from agents.spam_detector_agent import SpamDetectorAgent
        
        doc_agent = DocumentPreservationAgent()
        classifier_agent = ClassifierAgent()
        spam_agent = SpamDetectorAgent()
        
        print(f"   ✅ Document Preservation Agent ready")
        print(f"   ✅ Classifier Agent ready")
        print(f"   ✅ Spam Detector Agent ready")
        if doc_agent.vip_emails:
            print(f"   🔒 VIP Protection: {len(doc_agent.vip_emails)} email(s)")
        
        # Get inbox stats
        print("\n" + "="*100)
        stats = connector.get_inbox_stats()
        
        # Test on Other inbox (where all agents are most useful)
        print("\n" + "="*100)
        print("🎯 TESTING ALL AGENTS ON OTHER INBOX")
        print("="*100)
        
        other_emails = connector.get_emails(limit=1000, inbox_type='other')
        
        if not other_emails:
            print("❌ No emails fetched!")
            return
        
        print(f"\n🔍 Analyzing {len(other_emails)} emails with all 3 agents...\n")
        
        # Collect results from all agents
        combined_results = []
        
        for i, email in enumerate(other_emails, 1):
            subject = email.get('subject', 'No Subject')[:60]
            
            # Agent 1: Document Preservation
            doc_analysis = doc_agent.analyze_email(email)
            
            # Agent 2: Classifier
            classification = classifier_agent.classify_email(email)
            
            # Agent 3: Spam Detector
            spam_analysis = spam_agent.detect_spam(email)
            
            combined_results.append({
                'email': email,
                'document': doc_analysis,
                'classification': classification,
                'spam': spam_analysis
            })
            
            # Display combined analysis
            preserve_icon = "🛡️" if doc_analysis['should_preserve'] else "  "
            category_icons = {
                'urgent': '🚨', 'personal': '📧', 'newsletter': '📰',
                'promotional': '🛍️', 'informational': '📋', 'spam': '⚠️'
            }
            cat_icon = category_icons.get(classification['category'], '📧')
            spam_icon = "⚠️" if spam_analysis['is_spam'] else "✅"
            
            print(f"{i}. {preserve_icon} {cat_icon} {spam_icon} {subject}")
            print(f"   Preserve: {doc_analysis['should_preserve']} | Category: {classification['category']} | Spam Score: {spam_analysis['spam_score']}/100")
            print()
        
        # Generate summary statistics
        print("\n" + "="*100)
        print("📊 COMBINED ANALYSIS SUMMARY")
        print("="*100 + "\n")
        
        # Document Preservation Stats
        preserve_count = sum(1 for r in combined_results if r['document']['should_preserve'])
        print(f"🛡️ DOCUMENT PRESERVATION:")
        print(f"   To Preserve: {preserve_count} ({preserve_count/len(other_emails)*100:.1f}%)")
        print(f"   Safe to Process: {len(other_emails) - preserve_count} ({(len(other_emails) - preserve_count)/len(other_emails)*100:.1f}%)")
        
        # Classification Stats
        print(f"\n🏷️ CLASSIFICATION:")
        categories = {}
        for r in combined_results:
            cat = r['classification']['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            icon = category_icons.get(category, '📧')
            percentage = (count / len(other_emails)) * 100
            print(f"   {icon} {category.capitalize()}: {count} ({percentage:.1f}%)")
        
        # Spam Detection Stats
        spam_count = sum(1 for r in combined_results if r['spam']['is_spam'])
        uncertain_count = sum(1 for r in combined_results if r['spam']['is_spam'] and r['spam']['confidence'] != 'high')
        
        print(f"\n⚠️ SPAM DETECTION:")
        print(f"   Spam/Phishing: {spam_count} ({spam_count/len(other_emails)*100:.1f}%)")
        print(f"   Uncertain (needs review): {uncertain_count}")
        print(f"   Legitimate: {len(other_emails) - spam_count} ({(len(other_emails) - spam_count)/len(other_emails)*100:.1f}%)")
        
        # Cleanup Potential
        safe_to_delete = len([r for r in combined_results 
                            if not r['document']['should_preserve'] 
                            and r['classification']['category'] in ['newsletter', 'promotional', 'spam']
                            and not r['spam']['is_spam']])
        
        print(f"\n🗑️ CLEANUP POTENTIAL:")
        print(f"   Safe to delete: {safe_to_delete} emails ({safe_to_delete/len(other_emails)*100:.1f}%)")
        print(f"   (Newsletters/Promos that aren't documents or spam)")
        
        print("\n" + "="*100)
        print("✅ All Agents Analysis Complete!")
        print("="*100 + "\n")

def test_unwanted_agent_on_real_emails():
    """Test the Unwanted Agent on real emails"""
    
    print("="*100)
    print("🗑️ UNWANTED EMAIL AGENT - Real Email Analysis")
    print("="*100 + "\n")
    
    # Initialize components
    print("📧 Connecting to Outlook...")
    connector = OutlookConnector()
    
    if not connector.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("\n🤖 Initializing Unwanted Agent...")
    from agents.unwanted_agent import UnwantedAgent
    agent = UnwantedAgent()
    
    # Get inbox stats
    print("\n" + "="*100)
    stats = connector.get_inbox_stats()
    
    # Test on Other inbox (where unwanted emails are most common)
    print("\n" + "="*100)
    print("🎯 TESTING UNWANTED AGENT ON OTHER INBOX")
    print("="*100)
    
    other_emails = connector.get_emails(limit=1000, inbox_type='other')
    
    if not other_emails:
        print("❌ No emails fetched!")
        return
    
    print(f"\n🔍 Analyzing {len(other_emails)} emails for unwanted content...\n")
    
    results = agent.batch_analyze_unwanted(other_emails)
    
    # Generate detailed statistics
    print("\n" + "="*100)
    print("📊 UNWANTED EMAIL ANALYSIS RESULTS")
    print("="*100 + "\n")
    
    print(f"🗑️ UNWANTED EMAILS: {len(results['unwanted'])}")
    print(f"⚠️ UNCERTAIN (needs review): {len(results['uncertain'])}")
    print(f"✅ WANTED EMAILS: {len(results['wanted'])}")
    
    # Age breakdown for unwanted emails
    if results['unwanted']:
        print(f"\n📅 UNWANTED EMAIL AGE BREAKDOWN:")
        age_groups = {'2+ years': 0, '1-2 years': 0, '6-12 months': 0, '0-6 months': 0}
        
        for item in results['unwanted']:
            age_days = item['analysis']['indicators']['age_days']
            if age_days >= 730:
                age_groups['2+ years'] += 1
            elif age_days >= 365:
                age_groups['1-2 years'] += 1
            elif age_days >= 180:
                age_groups['6-12 months'] += 1
            else:
                age_groups['0-6 months'] += 1
        
        for age_range, count in age_groups.items():
            if count > 0:
                print(f"   {age_range}: {count} emails")
    
    # Pattern breakdown
    if results['unwanted']:
        print(f"\n🏷️ UNWANTED EMAIL PATTERNS:")
        pattern_counts = {
            'newsletter': 0,
            'social': 0,
            'marketing': 0,
            'event': 0
        }
        
        for item in results['unwanted']:
            patterns = item['analysis']['indicators'].get('patterns', {})
            for pattern_type, found in patterns.items():
                if found:
                    pattern_counts[pattern_type] += 1
        
        for pattern_type, count in pattern_counts.items():
            if count > 0:
                print(f"   {pattern_type.capitalize()}: {count} emails")
    
    # Cleanup potential
    unwanted_percentage = (len(results['unwanted']) / len(other_emails)) * 100
    
    print(f"\n🗑️ CLEANUP POTENTIAL:")
    print(f"   Unwanted: {len(results['unwanted'])} emails ({unwanted_percentage:.1f}%)")
    print(f"   Extrapolated to full 'Other' inbox ({stats['other']:,} emails):")
    extrapolated = int((len(results['unwanted']) / len(other_emails)) * stats['other'])
    print(f"   → Potentially ~{extrapolated:,} unwanted emails could be cleaned up!")
    
    print("\n" + "="*100)
    print("✅ Unwanted Agent Analysis Complete!")
    print("="*100 + "\n")

def test_multi_agent_on_real_emails():
    """Test the Multi-Agent Orchestrator on real emails"""
    
    print("="*100)
    print("🎭 MULTI-AGENT ORCHESTRATOR - Real Email Analysis")
    print("="*100 + "\n")
    
    # Initialize components
    print("📧 Connecting to Outlook...")
    connector = OutlookConnector()
    
    if not connector.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("\n🤖 Initializing Multi-Agent Orchestrator...")
    from core.multi_agent_orchestrator import MultiAgentOrchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Get inbox stats
    print("\n" + "="*100)
    stats = connector.get_inbox_stats()
    
    # Test on Other inbox
    print("\n" + "="*100)
    print("🎯 TESTING MULTI-AGENT SYSTEM ON OTHER INBOX")
    print("="*100)
    
    other_emails = connector.get_emails(limit=1000, inbox_type='other')
    
    if not other_emails:
        print("❌ No emails fetched!")
        return
    
    print(f"\n🔄 Running multi-agent analysis on {len(other_emails)} emails...\n")
    
    results = orchestrator.batch_analyze(other_emails)
    
    # Generate detailed statistics
    print("\n" + "="*100)
    print("📊 MULTI-AGENT ORCHESTRATION RESULTS")
    print("="*100 + "\n")
    
    print(f"🛡️ PRESERVE: {len(results['preserve'])} emails")
    print(f"🗑️ DELETE: {len(results['delete'])} emails")
    print(f"👁️ REVIEW: {len(results['review'])} emails")
    
    # Breakdown of preserve reasons
    if results['preserve']:
        print(f"\n🛡️ PRESERVE BREAKDOWN:")
        preserve_reasons = {}
        for item in results['preserve']:
            analysis = item['analysis']
            if analysis['document_analysis'].get('should_preserve'):
                preserve_reasons['Important Documents'] = preserve_reasons.get('Important Documents', 0) + 1
            elif analysis['classification']['category'] == 'personal':
                preserve_reasons['Personal Emails'] = preserve_reasons.get('Personal Emails', 0) + 1
            elif analysis['classification']['category'] == 'urgent':
                preserve_reasons['Urgent Emails'] = preserve_reasons.get('Urgent Emails', 0) + 1
            else:
                preserve_reasons['Other'] = preserve_reasons.get('Other', 0) + 1
        
        for reason, count in preserve_reasons.items():
            print(f"   {reason}: {count}")
    
    # Breakdown of delete reasons
    if results['delete']:
        print(f"\n🗑️ DELETE BREAKDOWN:")
        delete_categories = {}
        for item in results['delete']:
            category = item['analysis']['classification']['category']
            delete_categories[category] = delete_categories.get(category, 0) + 1
        
        for category, count in delete_categories.items():
            print(f"   {category.capitalize()}: {count}")
    
    # Breakdown of review reasons
    if results['review']:
        print(f"\n👁️ REVIEW BREAKDOWN:")
        review_reasons = {}
        for item in results['review']:
            analysis = item['analysis']
            if analysis['spam_analysis'].get('is_spam'):
                review_reasons['Spam/Phishing'] = review_reasons.get('Spam/Phishing', 0) + 1
            elif analysis['confidence'] == 'low':
                review_reasons['Low Confidence'] = review_reasons.get('Low Confidence', 0) + 1
            else:
                review_reasons['Other'] = review_reasons.get('Other', 0) + 1
        
        for reason, count in review_reasons.items():
            print(f"   {reason}: {count}")
    
    # Cleanup potential
    delete_percentage = (len(results['delete']) / len(other_emails)) * 100
    
    print(f"\n🗑️ CLEANUP POTENTIAL:")
    print(f"   Safe to delete: {len(results['delete'])} emails ({delete_percentage:.1f}%)")
    print(f"   Extrapolated to full 'Other' inbox ({stats['other']:,} emails):")
    extrapolated = int((len(results['delete']) / len(other_emails)) * stats['other'])
    print(f"   → Potentially ~{extrapolated:,} emails could be safely deleted!")
    
    print(f"\n🛡️ PROTECTION STATUS:")
    preserve_percentage = (len(results['preserve']) / len(other_emails)) * 100
    print(f"   Protected: {len(results['preserve'])} emails ({preserve_percentage:.1f}%)")
    
    print(f"\n👁️ HUMAN REVIEW NEEDED:")
    review_percentage = (len(results['review']) / len(other_emails)) * 100
    print(f"   Needs review: {len(results['review'])} emails ({review_percentage:.1f}%)")
    
    print("\n" + "="*100)
    print("✅ Multi-Agent Orchestration Complete!")
    print("="*100 + "\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'classify':
            test_classifier_on_real_emails()
        elif sys.argv[1] == 'all':
            test_all_agents_on_real_emails()
        elif sys.argv[1] == 'unwanted':
            test_unwanted_agent_on_real_emails()
        elif sys.argv[1] == 'multi':
            test_multi_agent_on_real_emails()
        else:
            test_agent_on_real_emails()
    else:
        test_agent_on_real_emails()
    
    