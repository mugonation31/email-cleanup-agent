"""
Classifier Agent
Categorizes emails into different types for targeted cleanup
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import OPENAI_API_KEY
import json

class ClassifierAgent:
    """Agent that classifies emails into categories"""
    
    def __init__(self):
        """Initialize the agent with OpenAI"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Email categories
        self.categories = {
            'urgent': '🚨 Requires immediate attention',
            'personal': '📧 From real people (not automated)',
            'newsletter': '📰 Newsletters, subscriptions',
            'promotional': '🛍️ Marketing, sales, offers',
            'informational': '📋 Notifications, updates, confirmations',
            'spam': '⚠️ Suspicious or unwanted'
        }
        
        # Urgent indicators
        self.urgent_keywords = [
            'urgent', 'immediate', 'action required', 'deadline',
            'expires', 'final notice', 'overdue', 'asap'
        ]

    def classify_email(self, email):
        """
        Classify an email into a category
        
        Args:
            email (dict): Email object with subject, from, bodyPreview, hasAttachments
            
        Returns:
            dict: Classification result with category, confidence, and reasoning
        """
        subject = email.get('subject', '')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', '')
        sender_name = sender.get('name', '')
        body_preview = email.get('bodyPreview', '')[:300]
        has_attachments = email.get('hasAttachments', False)
        
        # Quick checks for obvious categories
        
        # Check for urgent keywords
        subject_lower = subject.lower()
        if any(keyword in subject_lower for keyword in self.urgent_keywords):
            return {
                'category': 'urgent',
                'confidence': 'high',
                'reasoning': f"Subject contains urgent indicator: '{subject}'",
                'method': 'keyword_match'
            }
        
        # Check for automated senders (common patterns)
        automated_patterns = [
            'noreply', 'no-reply', 'donotreply', 'notifications',
            'automated', 'auto@', 'bounce', 'mailer-daemon'
        ]
        
        sender_lower = sender_email.lower()
        if any(pattern in sender_lower for pattern in automated_patterns):
            # It's automated, now determine what type
            return self._classify_automated_email(email)
        
        # Use AI for more nuanced classification
        return self._ai_classification(email)
    
    def _classify_automated_email(self, email):
        """Quick classification for obviously automated emails"""
        subject = email.get('subject', '').lower()
        body = email.get('bodyPreview', '').lower()
        
        # Newsletter indicators
        newsletter_keywords = ['unsubscribe', 'newsletter', 'weekly digest', 'update']
        if any(kw in subject or kw in body for kw in newsletter_keywords):
            return {
                'category': 'newsletter',
                'confidence': 'high',
                'reasoning': 'Automated newsletter or subscription email',
                'method': 'pattern_match'
            }
        
        # Promotional indicators
        promo_keywords = ['sale', 'offer', 'discount', 'deal', 'save', 'shop']
        if any(kw in subject or kw in body for kw in promo_keywords):
            return {
                'category': 'promotional',
                'confidence': 'high',
                'reasoning': 'Automated promotional or marketing email',
                'method': 'pattern_match'
            }
        
        # Default to informational for other automated emails
        return {
            'category': 'informational',
            'confidence': 'medium',
            'reasoning': 'Automated notification or system message',
            'method': 'pattern_match'
        }
    
    def _ai_classification(self, email):
        """Use GPT-4 to classify emails that need nuanced understanding"""
        
        subject = email.get('subject', 'No Subject')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', 'Unknown')
        sender_name = sender.get('name', 'Unknown')
        body_preview = email.get('bodyPreview', '')[:300]
        has_attachments = email.get('hasAttachments', False)
        
        system_prompt = """You are an email classification expert. Categorize emails into one of these categories:

        **Categories:**
        - urgent: Requires immediate attention (deadlines, action required, time-sensitive)
        - personal: From a real human writing specifically to the recipient (not automated)
        - newsletter: Subscriptions, newsletters, regular updates from organizations
        - promotional: Marketing, sales, offers, advertisements
        - informational: Notifications, confirmations, receipts, automated updates
        - spam: Suspicious, unwanted, or potentially harmful

        CRITICAL: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

        Respond ONLY with this exact JSON format:
        {
            "category": "urgent/personal/newsletter/promotional/informational/spam",
            "confidence": "high/medium/low",
            "reasoning": "1-2 sentence explanation of why this email fits this category. Be specific about what made you choose this category."
        }

        Example good reasoning: "This is a personal email from a colleague discussing a specific project meeting. The conversational tone and specific details indicate it was written by a real person."
        Example bad reasoning: "Looks like spam."
        """

        user_prompt = f"""Classify this email:

        Subject: {subject}
        From: {sender_name} <{sender_email}>
        Has Attachments: {has_attachments}
        Preview: {body_preview}

        Which category does this email belong to?"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Use JSON mode to guarantee valid JSON response
            response = self.llm.invoke(
                messages,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.content)
            result['method'] = 'ai_classification'
            
            return result
            
        except Exception as e:
            print(f"⚠️ AI classification error: {e}")
            # Default to informational if uncertain
            return {
                'category': 'informational',
                'confidence': 'low',
                'reasoning': 'Error in classification - defaulted to informational',
                'method': 'error_default',
                'error': str(e)
            }
    
    def batch_classify(self, emails):
        """
        Classify multiple emails
        
        Args:
            emails (list): List of email objects
            
        Returns:
            dict: Results grouped by category
        """
        results = {
            'urgent': [],
            'personal': [],
            'newsletter': [],
            'promotional': [],
            'informational': [],
            'spam': []
        }
        
        print(f"\n🔍 Classifying {len(emails)} emails...\n")
        
        for i, email in enumerate(emails, 1):
            classification = self.classify_email(email)
            
            email_info = {
                'email': email,
                'classification': classification
            }
            
            category = classification['category']
            results[category].append(email_info)
            
            # Get category icon
            category_icons = {
                'urgent': '🚨',
                'personal': '📧',
                'newsletter': '📰',
                'promotional': '🛍️',
                'informational': '📋',
                'spam': '⚠️'
            }
            
            icon = category_icons.get(category, '📧')
            subject = email.get('subject', 'No Subject')[:50]
            
            print(f"{i}. {icon} {category.upper()} - {subject}")
            print(f"   Reasoning: {classification['reasoning']}")
            print(f"   Method: {classification['method']} | Confidence: {classification['confidence']}")
            print()
        
        return results


# Test the agent
if __name__ == "__main__":
    print("="*100)
    print("🏷️ CLASSIFIER AGENT - Test")
    print("="*100 + "\n")
    
    # Test with sample emails
    test_emails = [
        {
            'subject': 'URGENT: Project deadline tomorrow',
            'from': {'emailAddress': {'address': 'boss@company.com', 'name': 'Your Boss'}},
            'bodyPreview': 'We need to finalize the presentation by end of day tomorrow.',
            'hasAttachments': True
        },
        {
            'subject': 'Lunch next week?',
            'from': {'emailAddress': {'address': 'friend@gmail.com', 'name': 'John Smith'}},
            'bodyPreview': 'Hey! Long time no see. Want to grab lunch next Tuesday?',
            'hasAttachments': False
        },
        {
            'subject': 'Your weekly tech digest',
            'from': {'emailAddress': {'address': 'newsletter@techcrunch.com', 'name': 'TechCrunch'}},
            'bodyPreview': 'Top stories this week in technology. Unsubscribe anytime.',
            'hasAttachments': False
        },
        {
            'subject': '50% OFF - Summer Sale!',
            'from': {'emailAddress': {'address': 'offers@store.com', 'name': 'Online Store'}},
            'bodyPreview': 'Exclusive deals just for you! Shop now and save big.',
            'hasAttachments': False
        },
        {
            'subject': 'Your Amazon order has shipped',
            'from': {'emailAddress': {'address': 'no-reply@amazon.com', 'name': 'Amazon'}},
            'bodyPreview': 'Your order #12345 is on the way. Track your package.',
            'hasAttachments': False
        },
        {
            'subject': 'You won the lottery!!!',
            'from': {'emailAddress': {'address': 'winner@suspicious.com', 'name': 'Lottery'}},
            'bodyPreview': 'Congratulations! Click here to claim your $1,000,000 prize.',
            'hasAttachments': False
        }
    ]
    
    agent = ClassifierAgent()
    results = agent.batch_classify(test_emails)
    
    print("\n" + "="*100)
    print("📊 CLASSIFICATION SUMMARY")
    print("="*100)
    for category, items in results.items():
        if items:
            icon = {'urgent': '🚨', 'personal': '📧', 'newsletter': '📰', 
                   'promotional': '🛍️', 'informational': '📋', 'spam': '⚠️'}[category]
            print(f"{icon} {category.upper()}: {len(items)}")
    print("="*100 + "\n")