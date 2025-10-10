"""
Unwanted Email Agent
Identifies legitimate but unwanted emails using ReAct pattern (Reasoning + Acting)
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import OPENAI_API_KEY
import json
from datetime import datetime, timedelta

class UnwantedAgent:
    """Agent that identifies unwanted but legitimate emails"""
    
    def __init__(self):
        """Initialize the agent with OpenAI"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Unwanted email categories
        self.unwanted_categories = {
            'newsletter_fatigue': 'Subscriptions you never read',
            'promotional_overload': 'Marketing emails you ignore',
            'social_noise': 'Social media notifications',
            'old_receipts': 'Automated receipts/confirmations',
            'expired_events': 'Past event invites',
            'job_alerts': 'Old job alerts (if you found a job)',
            'subscription_updates': 'Service updates you dont need'
        }
        
        # Patterns that indicate unwanted emails
        self.unwanted_patterns = {
            'newsletter_keywords': [
                'newsletter', 'weekly digest', 'monthly update', 'unsubscribe',
                'this weeks', 'latest news', 'whats new'
            ],
            'social_keywords': [
                'mentioned you', 'liked your', 'commented on', 'tagged you',
                'friend request', 'connection request', 'viewed your profile'
            ],
            'marketing_keywords': [
                'exclusive offer', 'limited time', 'dont miss', 'last chance',
                'flash sale', 'special deal', 'save now', 'shop now'
            ],
            'event_keywords': [
                'event reminder', 'rsvp', 'invitation', 'join us',
                'save the date', 'register now'
            ]
        }
        
        # Age thresholds (emails older than this might be unwanted)
        self.age_thresholds = {
            'receipts': 365,  # 1 year
            'newsletters': 180,  # 6 months
            'events': 30,  # 1 month
            'job_alerts': 90,  # 3 months
            'social': 90  # 3 months
        }
    
    def check_unwanted_patterns(self, subject, body):
        """Check for unwanted email patterns"""
        text = f"{subject} {body}".lower()
        
        found_patterns = {
            'newsletter': False,
            'social': False,
            'marketing': False,
            'event': False
        }
        
        # Check each pattern type
        for keyword in self.unwanted_patterns['newsletter_keywords']:
            if keyword in text:
                found_patterns['newsletter'] = True
                break
        
        for keyword in self.unwanted_patterns['social_keywords']:
            if keyword in text:
                found_patterns['social'] = True
                break
        
        for keyword in self.unwanted_patterns['marketing_keywords']:
            if keyword in text:
                found_patterns['marketing'] = True
                break
        
        for keyword in self.unwanted_patterns['event_keywords']:
            if keyword in text:
                found_patterns['event'] = True
                break
        
        return found_patterns
    
    def calculate_email_age_days(self, received_date):
        """Calculate how old an email is in days"""
        try:
            # Parse the date from the email
            if isinstance(received_date, str):
                # Format: 2016-01-09
                email_date = datetime.strptime(received_date[:10], '%Y-%m-%d')
            else:
                email_date = received_date
            
            today = datetime.now()
            age_days = (today - email_date).days
            return age_days
        except:
            return 0
    
    def is_too_old(self, age_days, category):
        """Check if email is too old based on category"""
        threshold = self.age_thresholds.get(category, 365)
        return age_days > threshold
    
    def calculate_unwanted_score(self, indicators):
        """Calculate unwanted score based on indicators"""
        score = 0
        reasons = []
        
        # Pattern matches (medium weight)
        if indicators.get('patterns', {}).get('newsletter'):
            score += 30
            reasons.append("Newsletter pattern detected")
        
        if indicators.get('patterns', {}).get('social'):
            score += 25
            reasons.append("Social media notification")
        
        if indicators.get('patterns', {}).get('marketing'):
            score += 35
            reasons.append("Marketing/promotional content")
        
        if indicators.get('patterns', {}).get('event'):
            score += 20
            reasons.append("Event-related email")
        
        # Age factor (high weight if very old)
        age_days = indicators.get('age_days', 0)
        if age_days > 730:  # 2+ years
            score += 40
            reasons.append(f"Very old email ({age_days} days / {age_days//365} years)")
        elif age_days > 365:  # 1+ years
            score += 25
            reasons.append(f"Old email ({age_days} days / {age_days//365} years)")
        elif age_days > 180:  # 6+ months
            score += 15
            reasons.append(f"Aging email ({age_days} days)")
        
        # Unread status (low weight)
        if indicators.get('is_unread'):
            score += 10
            reasons.append("Never opened")
        
        # Determine confidence
        if score >= 70:
            confidence = 'high'
        elif score >= 40:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return score, confidence, reasons
    
    def analyze_unwanted(self, email):
        """
        Analyze an email to determine if it's unwanted
        Uses ReAct pattern: Reasoning + Acting
        
        Args:
            email (dict): Email object with subject, from, bodyPreview, receivedDateTime
            
        Returns:
            dict: Analysis with is_unwanted, confidence, score, and reasoning
        """
        subject = email.get('subject', '')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', '')
        sender_name = sender.get('name', '')
        body_preview = email.get('bodyPreview', '')
        received_date = email.get('receivedDateTime', '')
        is_read = email.get('isRead', True)
        
        # Collect indicators
        indicators = {}
        
        # 1. Check unwanted patterns
        indicators['patterns'] = self.check_unwanted_patterns(subject, body_preview)
        
        # 2. Calculate age
        indicators['age_days'] = self.calculate_email_age_days(received_date)
        
        # 3. Check if unread
        indicators['is_unread'] = not is_read
        
        # Calculate unwanted score
        unwanted_score, confidence, reasons = self.calculate_unwanted_score(indicators)
        
        # If score is high, mark as unwanted immediately
        if unwanted_score >= 70:
            return {
                'is_unwanted': True,
                'confidence': 'high',
                'unwanted_score': unwanted_score,
                'reasoning': ' | '.join(reasons),
                'method': 'pattern_detection',
                'indicators': indicators
            }
        
        # If score is medium (40-69), use AI for reasoning (ReAct pattern)
        if 40 <= unwanted_score < 70:
            ai_result = self._ai_react_reasoning(email, indicators, unwanted_score, reasons)
            return ai_result
        
        # Low score - not unwanted
        return {
            'is_unwanted': False,
            'confidence': 'high',
            'unwanted_score': unwanted_score,
            'reasoning': 'Email appears relevant and recent',
            'method': 'pattern_detection',
            'indicators': indicators
        }
    
    def _ai_react_reasoning(self, email, indicators, unwanted_score, reasons):
        """
        Use ReAct pattern (Reasoning + Acting) for uncertain cases
        AI reasons about whether email is unwanted, then decides action
        """
        
        subject = email.get('subject', 'No Subject')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', 'Unknown')
        sender_name = sender.get('name', 'Unknown')
        body_preview = email.get('bodyPreview', '')[:300]
        age_days = indicators.get('age_days', 0)
        is_unread = indicators.get('is_unread', False)
        
        system_prompt = """You are an email cleanup expert using the ReAct pattern (Reasoning + Acting).

Your job is to REASON about whether an email is unwanted, then ACT on that reasoning.

UNWANTED emails are:
- Newsletters you never read
- Marketing emails you ignore
- Old social media notifications
- Automated receipts/confirmations (old)
- Event invites that have passed
- Job alerts (if old and unread)

NOT UNWANTED (keep these):
- Personal emails from real people
- Important notifications
- Recent receipts/confirmations
- Active subscriptions you engage with
- Work-related emails

CRITICAL: You must respond with ONLY valid JSON.

Use ReAct pattern:
1. REASON: Think about what this email is and whether it's useful
2. ACT: Decide to mark as unwanted or keep

Respond ONLY with this JSON format:
{
    "is_unwanted": true/false,
    "confidence": "high/medium/low",
    "reasoning": "REASON: [Your reasoning about the email] ACT: [Your decision and why]",
    "category": "newsletter_fatigue/promotional_overload/social_noise/old_receipts/expired_events/job_alerts/subscription_updates/keep"
}

Example reasoning: "REASON: This is a 2-year-old job alert that was never opened, suggesting the user found employment or is no longer interested in these positions. ACT: Mark as unwanted - old job alerts are cleanup candidates."
"""

        user_prompt = f"""Analyze this email using ReAct (Reasoning + Acting):

Subject: {subject}
From: {sender_name} <{sender_email}>
Age: {age_days} days ({age_days//365} years, {age_days%365} days)
Unread: {is_unread}
Preview: {body_preview}

Pattern Analysis Results:
Unwanted Score: {unwanted_score}/100 (threshold: 70)
Indicators: {' | '.join(reasons)}

REASON about this email, then ACT on your reasoning.
Is this unwanted?"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Use JSON mode
            response = self.llm.invoke(
                messages,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.content)
            result['unwanted_score'] = unwanted_score
            result['method'] = 'ai_react_reasoning'
            result['indicators'] = indicators
            
            # Enhance reasoning with pattern score
            if reasons:
                result['reasoning'] = f"{result['reasoning']} [Pattern score: {unwanted_score}]"
            
            return result
            
        except Exception as e:
            print(f"⚠️ AI ReAct reasoning error: {e}")
            # Default to unwanted if score was borderline and AI fails
            return {
                'is_unwanted': unwanted_score >= 55,
                'confidence': 'low',
                'unwanted_score': unwanted_score,
                'reasoning': f'Error in AI reasoning - defaulted based on score ({unwanted_score})',
                'method': 'error_default',
                'error': str(e),
                'indicators': indicators
            }
    
    def batch_analyze_unwanted(self, emails):
        """
        Analyze multiple emails for unwanted content
        
        Args:
            emails (list): List of email objects
            
        Returns:
            dict: Results with unwanted and wanted email lists
        """
        results = {
            'unwanted': [],
            'wanted': [],
            'uncertain': []
        }
        
        print(f"\n🔍 Analyzing {len(emails)} emails for unwanted content...\n")
        
        for i, email in enumerate(emails, 1):
            analysis = self.analyze_unwanted(email)
            
            email_info = {
                'email': email,
                'analysis': analysis
            }
            
            # Categorize based on result
            if analysis['is_unwanted']:
                if analysis['confidence'] == 'high':
                    results['unwanted'].append(email_info)
                    status = "🗑️ UNWANTED"
                else:
                    results['uncertain'].append(email_info)
                    status = "⚠️ LIKELY UNWANTED (uncertain)"
            else:
                results['wanted'].append(email_info)
                status = "✅ WANTED"
            
            subject = email.get('subject', 'No Subject')[:50]
            unwanted_score = analysis.get('unwanted_score', 0)
            age_days = analysis.get('indicators', {}).get('age_days', 0)
            
            print(f"{i}. {status} - {subject}")
            print(f"   Score: {unwanted_score}/100 | Age: {age_days} days | Confidence: {analysis['confidence']}")
            print(f"   Reasoning: {analysis['reasoning']}")
            print(f"   Method: {analysis['method']}")
            print()
        
        return results


# Test the agent
if __name__ == "__main__":
    print("="*100)
    print("🗑️ UNWANTED EMAIL AGENT - Test")
    print("="*100 + "\n")
    
    # Test with sample emails of varying ages
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    test_emails = [
        {
            'subject': 'Your weekly tech newsletter',
            'from': {'emailAddress': {'address': 'newsletter@techcrunch.com', 'name': 'TechCrunch'}},
            'bodyPreview': 'Top stories this week. Unsubscribe anytime.',
            'receivedDateTime': (today - timedelta(days=800)).isoformat(),  # 2+ years old
            'isRead': False
        },
        {
            'subject': 'Job Alert: Senior Developer positions',
            'from': {'emailAddress': {'address': 'alerts@indeed.com', 'name': 'Indeed'}},
            'bodyPreview': 'New job matches for you!',
            'receivedDateTime': (today - timedelta(days=400)).isoformat(),  # 1+ year old
            'isRead': False
        },
        {
            'subject': 'Someone liked your post',
            'from': {'emailAddress': {'address': 'notify@facebook.com', 'name': 'Facebook'}},
            'bodyPreview': 'John Smith liked your photo.',
            'receivedDateTime': (today - timedelta(days=200)).isoformat(),  # 6+ months
            'isRead': False
        },
        {
            'subject': 'Your monthly statement is ready',
            'from': {'emailAddress': {'address': 'statements@bank.com', 'name': 'Your Bank'}},
            'bodyPreview': 'View your latest bank statement online.',
            'receivedDateTime': (today - timedelta(days=15)).isoformat(),  # Recent
            'isRead': True
        },
        {
            'subject': 'FLASH SALE - 70% OFF Everything!',
            'from': {'emailAddress': {'address': 'deals@store.com', 'name': 'Online Store'}},
            'bodyPreview': 'Limited time offer! Shop now before it ends.',
            'receivedDateTime': (today - timedelta(days=500)).isoformat(),  # Old promo
            'isRead': False
        },
        {
            'subject': 'Meeting notes from our call',
            'from': {'emailAddress': {'address': 'colleague@work.com', 'name': 'Sarah'}},
            'bodyPreview': 'Hi! Here are the notes from today. Let me know if I missed anything.',
            'receivedDateTime': (today - timedelta(days=5)).isoformat(),  # Recent
            'isRead': True
        }
    ]
    
    agent = UnwantedAgent()
    results = agent.batch_analyze_unwanted(test_emails)
    
    print("\n" + "="*100)
    print("📊 UNWANTED EMAIL ANALYSIS SUMMARY")
    print("="*100)
    print(f"🗑️ Unwanted: {len(results['unwanted'])}")
    print(f"⚠️ Uncertain: {len(results['uncertain'])}")
    print(f"✅ Wanted: {len(results['wanted'])}")
    print("="*100 + "\n")