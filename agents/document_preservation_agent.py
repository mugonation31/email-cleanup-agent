"""
Document Preservation Agent
Identifies and protects important documents from deletion
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import OPENAI_API_KEY, VIP_EMAILS
import json

class DocumentPreservationAgent:
    """Agent that identifies important documents that must be preserved"""
    
    def __init__(self):
        """Initialize the agent with OpenAI"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            temperature=0,  # Deterministic for classification
            openai_api_key=OPENAI_API_KEY
        )
        
        # VIP emails from config
        self.vip_emails = VIP_EMAILS
        
        # Keywords that typically indicate important documents
        self.important_keywords = [
            'payslip', 'salary', 'wage', 'payment advice',
            'invoice', 'receipt', 'bill', 'statement',
            'tax', 'hmrc', 'p60', 'p45', 'tax return',
            'contract', 'agreement', 'offer letter',
            'insurance', 'policy', 'claim',
            'mortgage', 'loan', 'credit',
            'pension', 'retirement',
            'legal', 'court', 'solicitor',
            'medical', 'prescription', 'appointment',
            'passport', 'visa', 'immigration',
            'degree', 'certificate', 'transcript'
        ]
        
        # Important sender domains
        self.important_domains = [
            'gov.uk', 'hmrc.gov.uk',
            'payroll', 'hr',
            'bank', 'banking',
            'insurance',
            'legal', 'solicitor'
        ]

    def is_vip_sender(self, sender_email):
        """Check if email is from a VIP contact"""
        if not sender_email or not self.vip_emails:
            return False
        
        sender_lower = sender_email.lower().strip()
        return sender_lower in self.vip_emails
    
    def contains_important_keywords(self, text):
        """Check if text contains important keywords"""
        if not text:
            return False
        
        text_lower = text.lower()
        matches = [kw for kw in self.important_keywords if kw in text_lower]
        return len(matches) > 0, matches
    
    def is_important_sender(self, sender_email):
        """Check if sender is from an important domain"""
        if not sender_email:
            return False
        
        sender_lower = sender_email.lower()
        for domain in self.important_domains:
            if domain in sender_lower:
                return True
        return False
    
    def analyze_email(self, email):
        """
        Analyze an email to determine if it should be preserved
        
        Args:
            email (dict): Email object with subject, from, bodyPreview, hasAttachments
            
        Returns:
            dict: Analysis result with decision and reasoning
        """
        subject = email.get('subject', '')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', '')
        sender_name = sender.get('name', '')
        body_preview = email.get('bodyPreview', '')
        has_attachments = email.get('hasAttachments', False)
        
        # PRIORITY #1: Check VIP senders FIRST
        if self.is_vip_sender(sender_email):
            return {
                'should_preserve': True,
                'confidence': 'high',
                'reasoning': f"🔒 VIP Contact: {sender_name} ({sender_email})",
                'method': 'vip_contact',
                'sender': sender_email
            }
        
        # Quick keyword check
        subject_has_keywords, subject_matches = self.contains_important_keywords(subject)
        body_has_keywords, body_matches = self.contains_important_keywords(body_preview)
        is_important_sender = self.is_important_sender(sender_email)
        
        # If clear indicators, preserve immediately
        if subject_has_keywords or (body_has_keywords and has_attachments):
            return {
                'should_preserve': True,
                'confidence': 'high',
                'reasoning': f"Contains important keywords: {', '.join(set(subject_matches + body_matches))}",
                'method': 'keyword_match',
                'keywords_found': list(set(subject_matches + body_matches))
            }
        
        if is_important_sender and has_attachments:
            return {
                'should_preserve': True,
                'confidence': 'high',
                'reasoning': f"From important sender ({sender_email}) with attachments",
                'method': 'important_sender',
                'sender': sender_email
            }
        
        # If unsure, use AI to decide
        return self.ai_classification(email, {
            'subject_keywords': subject_matches,
            'body_keywords': body_matches,
            'important_sender': is_important_sender
        })

    def ai_classification(self, email, context):
        """Use GPT-4 to classify emails when keyword matching is uncertain"""
        
        subject = email.get('subject', 'No Subject')
        sender = email.get('from', {}).get('emailAddress', {})
        sender_email = sender.get('address', 'Unknown')
        sender_name = sender.get('name', 'Unknown')
        body_preview = email.get('bodyPreview', '')[:200]  # First 200 chars
        has_attachments = email.get('hasAttachments', False)
        
        system_prompt = """You are an email classification expert. Your job is to identify emails that contain important documents or information that should be preserved.

        Important categories include:
        - Financial: Payslips, invoices, receipts, bills, bank statements, tax documents
        - Legal: Contracts, agreements, legal notices
        - Medical: Prescriptions, appointment confirmations, medical records
        - Official: Government correspondence, insurance policies, identification documents
        - Employment: Job offers, employment contracts, HR documents
        - Education: Certificates, transcripts, qualifications

        Respond in JSON format with:
        {
            "should_preserve": true/false,
            "confidence": "high"/"medium"/"low",
            "reasoning": "brief explanation",
            "category": "financial"/"legal"/"medical"/"official"/"employment"/"education"/"other"
        }"""

        user_prompt = f"""Analyze this email and determine if it should be preserved:

        Subject: {subject}
        From: {sender_name} <{sender_email}>
        Has Attachments: {has_attachments}
        Preview: {body_preview}

        Context:
        - Keywords found in subject: {context.get('subject_keywords', [])}
        - Keywords found in body: {context.get('body_keywords', [])}
        - Important sender: {context.get('important_sender', False)}

        Should this email be preserved?"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content)
            result['method'] = 'ai_classification'
            
            return result
            
        except Exception as e:
            print(f"⚠️ AI classification error: {e}")
            # Default to preserving if uncertain
            return {
                'should_preserve': True,
                'confidence': 'low',
                'reasoning': 'Error in classification - preserving to be safe',
                'method': 'error_default',
                'error': str(e)
            }
        
    def batch_analyze(self, emails):
        """
        Analyze multiple emails
        
        Args:
            emails (list): List of email objects
            
        Returns:
            dict: Results with preserved and safe to delete lists
        """
        results = {
            'preserve': [],
            'safe_to_delete': [],
            'uncertain': []
        }
        
        print(f"\n🔍 Analyzing {len(emails)} emails...\n")
        
        for i, email in enumerate(emails, 1):
            analysis = self.analyze_email(email)
            
            email_info = {
                'email': email,
                'analysis': analysis
            }
            
            if analysis['should_preserve']:
                if analysis['confidence'] == 'high':
                    results['preserve'].append(email_info)
                    status = "✅ PRESERVE"
                else:
                    results['uncertain'].append(email_info)
                    status = "⚠️ UNCERTAIN"
            else:
                results['safe_to_delete'].append(email_info)
                status = "❌ SAFE TO DELETE"
            
            subject = email.get('subject', 'No Subject')[:50]
            print(f"{i}. {status} - {subject}")
            print(f"   Reasoning: {analysis['reasoning']}")
            print(f"   Method: {analysis['method']} | Confidence: {analysis['confidence']}")
            print()
        
        return results


# Test the agent
if __name__ == "__main__":
    print("="*100)
    print("🛡️ DOCUMENT PRESERVATION AGENT - Test")
    print("="*100 + "\n")
    
    # Show VIP protection status
    agent = DocumentPreservationAgent()
    if agent.vip_emails:
        print(f"🔒 VIP Protection Active: {len(agent.vip_emails)} email(s) protected")
        print(f"   Protected: {', '.join(agent.vip_emails)}")
    else:
        print("⚠️ No VIP emails configured")
    print()
    
    # Test with sample emails
    test_emails = [
        {
            'subject': 'Dinner plans tonight?',
            'from': {'emailAddress': {'address': 'wife@email.com', 'name': 'Your Wife'}},
            'bodyPreview': 'What time will you be home? Thinking of making pasta.',
            'hasAttachments': False
        },
        {
            'subject': 'Payslip Attached',
            'from': {'emailAddress': {'address': 'payroll@company.com', 'name': 'Payroll Dept'}},
            'bodyPreview': 'Your payslip for October 2024 is attached.',
            'hasAttachments': True
        },
        {
            'subject': 'Weekly Newsletter',
            'from': {'emailAddress': {'address': 'newsletter@marketing.com', 'name': 'Marketing Team'}},
            'bodyPreview': 'Check out this weeks top stories and updates.',
            'hasAttachments': False
        },
        {
            'subject': 'Invoice #12345',
            'from': {'emailAddress': {'address': 'billing@service.com', 'name': 'Billing'}},
            'bodyPreview': 'Thank you for your purchase. Invoice attached.',
            'hasAttachments': True
        }
    ]
    
    results = agent.batch_analyze(test_emails)
    
    print("\n" + "="*100)
    print("📊 ANALYSIS SUMMARY")
    print("="*100)
    print(f"✅ To Preserve: {len(results['preserve'])}")
    print(f"⚠️ Uncertain: {len(results['uncertain'])}")
    print(f"❌ Safe to Delete: {len(results['safe_to_delete'])}")
    print("="*100 + "\n")