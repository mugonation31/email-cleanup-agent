"""
Spam Detector Agent
Advanced spam and phishing detection using pattern recognition and AI
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import OPENAI_API_KEY
import json
import re

class SpamDetectorAgent:
    """Agent specialized in detecting spam, phishing, and suspicious emails"""
    
    def __init__(self):
        """Initialize the agent with OpenAI"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Spam indicators - common patterns
        self.spam_phrases = [
            'congratulations you won', 'claim your prize', 'click here now',
            'limited time offer', 'act now', 'urgent response required',
            'verify your account', 'confirm your identity', 'suspended account',
            'unusual activity', 'security alert', 'your account will be closed',
            'nigerian prince', 'inheritance', 'lottery winner',
            'make money fast', 'work from home', 'get rich quick',
            'free money', 'risk free', 'no credit check',
            'weight loss', 'male enhancement', 'buy medication',
            'unsubscribe impossible', 'this is not spam'
        ]
        
        # Suspicious sender patterns
        self.suspicious_sender_patterns = [
            r'@.*\.ru$',  # Russian domains (common for spam)
            r'@.*\.cn$',  # Chinese domains
            r'\d{5,}',    # Long number sequences in email
            r'[a-z]{20,}',  # Very long random strings
            r'admin@.*\.info$',  # Generic admin from .info domains
            r'support@.*\.xyz$',  # Support from uncommon TLDs
        ]
        
        # Phishing indicators
        self.phishing_keywords = [
            'verify', 'confirm', 'update', 'suspended', 'locked',
            'security alert', 'unusual activity', 'click here',
            'immediate action', 'account will be closed'
        ]
        
        # Known legitimate domains (whitelist)
        self.legitimate_domains = [
            'amazon.com', 'amazon.co.uk', 'paypal.com', 'ebay.com',
            'microsoft.com', 'google.com', 'apple.com', 'facebook.com',
            'linkedin.com', 'twitter.com', 'gov.uk', 'hmrc.gov.uk',
            'o2.co.uk', 'talktalk.co.uk', 'bt.com', 'sky.com'
        ]
    
    def is_legitimate_sender(self, sender_email):
        """Check if sender is from a known legitimate domain"""
        if not sender_email:
            return False
        
        sender_lower = sender_email.lower()
        for domain in self.legitimate_domains:
            if domain in sender_lower:
                return True
        return False
    
    def check_spam_phrases(self, text):
        """Check for common spam phrases in text"""
        if not text:
            return False, []
        
        text_lower = text.lower()
        found_phrases = [phrase for phrase in self.spam_phrases if phrase in text_lower]
        return len(found_phrases) > 0, found_phrases
    
    def check_suspicious_sender(self, sender_email):
        """Check if sender matches suspicious patterns"""
        if not sender_email:
            return False, None
        
        for pattern in self.suspicious_sender_patterns:
            if re.search(pattern, sender_email, re.IGNORECASE):
                return True, pattern
        return False, None
    
    def check_phishing_indicators(self, subject, body):
        """Check for phishing indicators"""
        combined_text = f"{subject} {body}".lower()
        
        phishing_count = sum(1 for keyword in self.phishing_keywords if keyword in combined_text)
        
        # Check for urgency + action required (common phishing combo)
        urgency_words = ['urgent', 'immediate', 'now', 'today', 'asap']
        action_words = ['click', 'verify', 'confirm', 'update', 'login']
        
        has_urgency = any(word in combined_text for word in urgency_words)
        has_action = any(word in combined_text for word in action_words)
        
        is_phishing = phishing_count >= 2 or (has_urgency and has_action)
        
        return is_phishing, phishing_count
    
    def calculate_spam_score(self, indicators):
        """Calculate spam score based on multiple indicators"""
        score = 0
        reasons = []
        
        # Spam phrases found (high weight)
        if indicators.get('spam_phrases'):
            score += 40
            reasons.append(f"Contains spam phrases: {', '.join(indicators['spam_phrases'][:3])}")
        
        # Suspicious sender (high weight)
        if indicators.get('suspicious_sender'):
            score += 35
            reasons.append(f"Suspicious sender pattern: {indicators['suspicious_sender_pattern']}")
        
        # Phishing indicators (medium-high weight)
        if indicators.get('phishing_indicators'):
            score += 25
            reasons.append(f"Phishing indicators detected ({indicators['phishing_count']} keywords)")
        
        # Not from legitimate domain (low weight)
        if not indicators.get('legitimate_sender'):
            score += 10
            reasons.append("Sender not from known legitimate domain")
        
        # Determine confidence based on score
        if score >= 60:
            confidence = 'high'
        elif score >= 35:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return score, confidence, reasons
    
    def detect_spam(self, email):
        """
        Analyze an email to detect spam
        
        Args:
            email (dict): Email object with subject, from, bodyPreview, hasAttachments
            
        Returns:
            dict: Spam analysis with is_spam, confidence, score, and reasoning
        """
        subject = email.get('subject', '')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', '')
        sender_name = sender.get('name', '')
        body_preview = email.get('bodyPreview', '')
        
        # Collect indicators
        indicators = {}
        
        # 1. Check if from legitimate domain
        indicators['legitimate_sender'] = self.is_legitimate_sender(sender_email)
        
        # 2. Check for spam phrases
        has_spam_phrases, spam_phrases = self.check_spam_phrases(f"{subject} {body_preview}")
        indicators['spam_phrases'] = spam_phrases if has_spam_phrases else []
        
        # 3. Check suspicious sender patterns
        is_suspicious, pattern = self.check_suspicious_sender(sender_email)
        indicators['suspicious_sender'] = is_suspicious
        indicators['suspicious_sender_pattern'] = pattern if is_suspicious else None
        
        # 4. Check phishing indicators
        is_phishing, phishing_count = self.check_phishing_indicators(subject, body_preview)
        indicators['phishing_indicators'] = is_phishing
        indicators['phishing_count'] = phishing_count
        
        # Calculate spam score
        spam_score, confidence, reasons = self.calculate_spam_score(indicators)
        
        # If score is high or medium, mark as spam
        is_spam = spam_score >= 35
        
        # If high confidence spam, return immediately
        if spam_score >= 60:
            return {
                'is_spam': True,
                'confidence': 'high',
                'spam_score': spam_score,
                'reasoning': ' | '.join(reasons),
                'method': 'pattern_detection',
                'indicators': indicators
            }
        
        # If medium score (35-59), use AI for final decision
        if 35 <= spam_score < 60:
            ai_result = self._ai_spam_detection(email, indicators, spam_score)
            return ai_result
        
        # Low score - not spam
        return {
            'is_spam': False,
            'confidence': 'high',
            'spam_score': spam_score,
            'reasoning': 'No significant spam indicators detected',
            'method': 'pattern_detection',
            'indicators': indicators
        }
    
    def _ai_spam_detection(self, email, indicators, spam_score):
        """Use GPT-4 for final spam determination on uncertain cases"""
        
        subject = email.get('subject', 'No Subject')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', 'Unknown')
        sender_name = sender.get('name', 'Unknown')
        body_preview = email.get('bodyPreview', '')[:300]
        
        system_prompt = """You are a spam detection expert. Analyze emails to determine if they are spam, phishing attempts, or legitimate.

CRITICAL: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

Consider these factors:
- Is the sender trustworthy?
- Does the content match common spam/phishing patterns?
- Is the message urgent or pressuring action?
- Are there suspicious links or requests?
- Does it seem like a legitimate business communication?

Respond ONLY with this exact JSON format:
{
    "is_spam": true/false,
    "confidence": "high/medium/low",
    "reasoning": "1-2 sentence explanation of why this is or isn't spam. Be specific about what indicators you found or didn't find."
}

Example good reasoning: "This email uses urgent language and requests account verification, which are common phishing tactics. The sender domain doesn't match the claimed company."
Example bad reasoning: "Looks like spam."
"""

        # Build context from indicators
        context_parts = []
        if indicators.get('spam_phrases'):
            context_parts.append(f"Contains spam phrases: {', '.join(indicators['spam_phrases'][:3])}")
        if indicators.get('suspicious_sender'):
            context_parts.append(f"Suspicious sender pattern detected")
        if indicators.get('phishing_indicators'):
            context_parts.append(f"Phishing keywords found ({indicators['phishing_count']})")
        if indicators.get('legitimate_sender'):
            context_parts.append("From known legitimate domain")
        
        context = ' | '.join(context_parts) if context_parts else "Mixed signals"

        user_prompt = f"""Analyze this email for spam/phishing:

Subject: {subject}
From: {sender_name} <{sender_email}>
Preview: {body_preview}

Pattern Analysis Results:
Spam Score: {spam_score}/100 (threshold: 60)
Indicators: {context}

This email scored in the uncertain range (35-59). 
Is this spam/phishing or legitimate?"""

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
            result['spam_score'] = spam_score
            result['method'] = 'ai_spam_detection'
            result['indicators'] = indicators
            
            # Combine AI reasoning with pattern detection findings
            if context_parts:
                result['reasoning'] = f"{result['reasoning']} [Pattern score: {spam_score}]"
            
            return result
            
        except Exception as e:
            print(f"⚠️ AI spam detection error: {e}")
            # Default to spam if score was borderline and AI fails
            return {
                'is_spam': spam_score >= 50,
                'confidence': 'low',
                'spam_score': spam_score,
                'reasoning': f'Error in AI classification - defaulted based on score ({spam_score})',
                'method': 'error_default',
                'error': str(e),
                'indicators': indicators
            }
    
    def batch_detect_spam(self, emails):
        """
        Analyze multiple emails for spam
        
        Args:
            emails (list): List of email objects
            
        Returns:
            dict: Results with spam and legitimate email lists
        """
        results = {
            'spam': [],
            'legitimate': [],
            'uncertain': []
        }
        
        print(f"\n🔍 Analyzing {len(emails)} emails for spam...\n")
        
        for i, email in enumerate(emails, 1):
            analysis = self.detect_spam(email)
            
            email_info = {
                'email': email,
                'analysis': analysis
            }
            
            # Categorize based on result
            if analysis['is_spam']:
                if analysis['confidence'] == 'high':
                    results['spam'].append(email_info)
                    status = "⚠️ SPAM"
                else:
                    results['uncertain'].append(email_info)
                    status = "⚠️ LIKELY SPAM (uncertain)"
            else:
                results['legitimate'].append(email_info)
                status = "✅ LEGITIMATE"
            
            subject = email.get('subject', 'No Subject')[:50]
            spam_score = analysis.get('spam_score', 0)
            
            print(f"{i}. {status} - {subject}")
            print(f"   Score: {spam_score}/100 | Confidence: {analysis['confidence']}")
            print(f"   Reasoning: {analysis['reasoning']}")
            print(f"   Method: {analysis['method']}")
            print()
        
        return results


# Test the agent
if __name__ == "__main__":
    print("="*100)
    print("⚠️ SPAM DETECTOR AGENT - Test")
    print("="*100 + "\n")
    
# Test with sample emails
    test_emails = [
        {
            'subject': 'Your Amazon order has shipped',
            'from': {'emailAddress': {'address': 'ship-confirm@amazon.com', 'name': 'Amazon'}},
            'bodyPreview': 'Your order #12345 is on the way. Track your package.',
            'hasAttachments': False
        },
        {
            'subject': 'URGENT: Verify your PayPal account NOW!!!',
            'from': {'emailAddress': {'address': 'security@paypa1.com', 'name': 'PayPal'}},
            'bodyPreview': 'Your account has been suspended. Click here immediately to verify your identity or your account will be closed.',
            'hasAttachments': False
        },
        {
            'subject': 'Congratulations! You won $1,000,000!!!',
            'from': {'emailAddress': {'address': 'winner123456@lottery.ru', 'name': 'International Lottery'}},
            'bodyPreview': 'You are the lucky winner! Claim your prize now by sending your bank details. Act fast, this offer expires today!',
            'hasAttachments': False
        },
        {
            'subject': 'Meeting notes from today',
            'from': {'emailAddress': {'address': 'colleague@company.com', 'name': 'John Colleague'}},
            'bodyPreview': 'Hi, here are the notes from our meeting this morning. Let me know if I missed anything.',
            'hasAttachments': True
        },
        {
            'subject': 'Important: Confirm your email address',
            'from': {'emailAddress': {'address': 'notifications@unknownservice.com', 'name': 'Account Services'}},
            'bodyPreview': 'Please verify your email address to continue using our service. Click the link below to confirm.',
            'hasAttachments': False
        },
        {
            'subject': 'Exclusive offer just for you!',
            'from': {'emailAddress': {'address': 'offers@store.com', 'name': 'Online Store'}},
            'bodyPreview': 'Limited time sale! 50% off everything. Shop now before it ends.',
            'hasAttachments': False
        },
        {
            'subject': 'Your O2 bill is ready',
            'from': {'emailAddress': {'address': 'billing@o2.co.uk', 'name': 'O2'}},
            'bodyPreview': 'Your latest bill is now available to view online.',
            'hasAttachments': False
        }
    ]
    
    agent = SpamDetectorAgent()
    results = agent.batch_detect_spam(test_emails)
    
    print("\n" + "="*100)
    print("📊 SPAM DETECTION SUMMARY")
    print("="*100)
    print(f"⚠️ Spam: {len(results['spam'])}")
    print(f"⚠️ Uncertain: {len(results['uncertain'])}")
    print(f"✅ Legitimate: {len(results['legitimate'])}")
    print("="*100 + "\n")