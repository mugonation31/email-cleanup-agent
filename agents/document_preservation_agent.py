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