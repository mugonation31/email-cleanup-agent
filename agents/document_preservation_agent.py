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