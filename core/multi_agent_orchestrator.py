"""
Multi-Agent Orchestrator using LangGraph
Coordinates all email analysis agents in a unified workflow
"""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from agents.document_preservation_agent import DocumentPreservationAgent
from agents.classifier_agent import ClassifierAgent
from agents.spam_detector_agent import SpamDetectorAgent
from agents.unwanted_agent import UnwantedAgent
import operator


# Define the state that will be passed between agents
class EmailAnalysisState(TypedDict):
    """State schema for email analysis workflow"""
    
    # Input
    email: dict  # The email being analyzed
    
    # Agent results
    document_analysis: dict  # From Document Preservation Agent
    classification: dict  # From Classifier Agent
    spam_analysis: dict  # From Spam Detector Agent
    unwanted_analysis: dict  # From Unwanted Agent
    
    # Final decision
    final_decision: str  # "preserve", "delete", "review"
    confidence: str  # "high", "medium", "low"
    reasoning_chain: Annotated[Sequence[str], operator.add]  # Track all reasoning
    

class MultiAgentOrchestrator:
    """Orchestrates multiple email analysis agents using LangGraph"""
    
    def __init__(self):
        """Initialize all agents and build the workflow graph"""
        
        # Initialize all agents
        print("🤖 Initializing agents...")
        self.doc_agent = DocumentPreservationAgent()
        self.classifier = ClassifierAgent()
        self.spam_detector = SpamDetectorAgent()
        self.unwanted_agent = UnwantedAgent()
        
        # Build the workflow graph
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()
        
        print("✅ Multi-agent orchestrator ready!")
        if self.doc_agent.vip_emails:
            print(f"🔒 VIP Protection: {len(self.doc_agent.vip_emails)} email(s)")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(EmailAnalysisState)
        
        # Add agent nodes
        workflow.add_node("document_agent", self._document_node)
        workflow.add_node("classifier", self._classifier_node)
        workflow.add_node("spam_detector", self._spam_node)
        workflow.add_node("unwanted_agent", self._unwanted_node)
        workflow.add_node("decision_maker", self._decision_node)
        
        # Define the workflow edges (order of execution)
        workflow.set_entry_point("document_agent")
        
        # Sequential workflow:
        # Document Agent → Classifier → Spam Detector → Unwanted → Decision
        workflow.add_edge("document_agent", "classifier")
        workflow.add_edge("classifier", "spam_detector")
        workflow.add_edge("spam_detector", "unwanted_agent")
        workflow.add_edge("unwanted_agent", "decision_maker")
        workflow.add_edge("decision_maker", END)
        
        return workflow
    
    def _document_node(self, state: EmailAnalysisState) -> EmailAnalysisState:
        """Node for Document Preservation Agent"""
        email = state["email"]
        
        analysis = self.doc_agent.analyze_email(email)
        
        # Add reasoning to chain
        decision = "PRESERVE" if analysis['should_preserve'] else "DON'T PRESERVE"
        reasoning = f"📄 Document Agent: {decision}"
        if analysis.get('reasoning'):
            reasoning += f" - {analysis['reasoning']}"
        
        return {
            **state,
            "document_analysis": analysis,
            "reasoning_chain": [reasoning]
        }
    
    def _classifier_node(self, state: EmailAnalysisState) -> EmailAnalysisState:
        """Node for Classifier Agent"""
        email = state["email"]
        
        classification = self.classifier.classify_email(email)
        
        # Add reasoning to chain
        category_icons = {
            'urgent': '🚨', 'personal': '📧', 'newsletter': '📰',
            'promotional': '🛍️', 'informational': '📋', 'spam': '⚠️'
        }
        icon = category_icons.get(classification['category'], '📧')
        reasoning = f"{icon} Classifier: {classification['category'].upper()} ({classification['confidence']})"
        
        return {
            **state,
            "classification": classification,
            "reasoning_chain": [reasoning]
        }
    
    def _spam_node(self, state: EmailAnalysisState) -> EmailAnalysisState:
        """Node for Spam Detector Agent"""
        email = state["email"]
        
        spam_analysis = self.spam_detector.detect_spam(email)
        
        # Add reasoning to chain
        if spam_analysis['is_spam']:
            reasoning = f"⚠️ Spam Detector: SPAM ({spam_analysis['spam_score']}/100)"
        else:
            reasoning = f"✅ Spam Detector: LEGITIMATE ({spam_analysis['spam_score']}/100)"
        
        return {
            **state,
            "spam_analysis": spam_analysis,
            "reasoning_chain": [reasoning]
        }
    
    def _unwanted_node(self, state: EmailAnalysisState) -> EmailAnalysisState:
        """Node for Unwanted Email Agent"""
        email = state["email"]
        
        unwanted_analysis = self.unwanted_agent.analyze_unwanted(email)
        
        # Add reasoning to chain
        age_days = unwanted_analysis.get('indicators', {}).get('age_days', 0)
        if unwanted_analysis['is_unwanted']:
            reasoning = f"🗑️ Unwanted Agent: UNWANTED (score: {unwanted_analysis['unwanted_score']}/100, age: {age_days} days)"
        else:
            reasoning = f"✅ Unwanted Agent: WANTED (score: {unwanted_analysis['unwanted_score']}/100)"
        
        return {
            **state,
            "unwanted_analysis": unwanted_analysis,
            "reasoning_chain": [reasoning]
        }
    def _decision_node(self, state: EmailAnalysisState) -> EmailAnalysisState:
        """
        The Judge: Makes final decision based on all agent inputs
        """
        doc_analysis = state["document_analysis"]
        classification = state["classification"]
        spam_analysis = state["spam_analysis"]
        unwanted_analysis = state["unwanted_analysis"]
        
        # Decision logic
        final_decision = "review"  # Default to review
        confidence = "medium"
        reasons = []
        
        # Rule 1: Document Agent says PRESERVE → Always preserve
        if doc_analysis['should_preserve']:
            final_decision = "preserve"
            confidence = doc_analysis['confidence']
            reasons.append("Document Agent: Important document detected")
        
        # Rule 2: Spam detected → Review (don't auto-delete spam, human should verify)
        elif spam_analysis['is_spam']:
            final_decision = "review"
            confidence = spam_analysis['confidence']
            reasons.append(f"Spam Detector: Spam/phishing detected ({spam_analysis['spam_score']}/100)")
        
        # Rule 3: Urgent or Personal → Preserve
        elif classification['category'] in ['urgent', 'personal']:
            final_decision = "preserve"
            confidence = classification['confidence']
            reasons.append(f"Classifier: {classification['category'].capitalize()} email")
        
        # Rule 4: Unwanted + Not important → Delete
        elif unwanted_analysis['is_unwanted'] and not doc_analysis['should_preserve']:
            # Only auto-delete if high confidence
            if unwanted_analysis['confidence'] == 'high' and classification['category'] in ['newsletter', 'promotional', 'informational']:
                final_decision = "delete"
                confidence = "high"
                reasons.append(f"Unwanted Agent: Old unwanted email ({unwanted_analysis['unwanted_score']}/100)")
            else:
                final_decision = "review"
                confidence = "medium"
                reasons.append("Unwanted but needs human review")
        
        # Rule 5: Low confidence from any agent → Review
        elif any([
            doc_analysis['confidence'] == 'low',
            classification['confidence'] == 'low',
            spam_analysis['confidence'] == 'low',
            unwanted_analysis['confidence'] == 'low'
        ]):
            final_decision = "review"
            confidence = "low"
            reasons.append("Low confidence from one or more agents")
        
        # Rule 6: Everything else → Preserve (safe default)
        else:
            final_decision = "preserve"
            confidence = "medium"
            reasons.append("No strong indicators for deletion")
        
        # Add final decision to reasoning chain
        decision_icons = {
            'preserve': '🛡️',
            'delete': '🗑️',
            'review': '👁️'
        }
        icon = decision_icons.get(final_decision, '❓')
        reasoning = f"{icon} FINAL DECISION: {final_decision.upper()} ({confidence} confidence) - {' | '.join(reasons)}"
        
        return {
            **state,
            "final_decision": final_decision,
            "confidence": confidence,
            "reasoning_chain": [reasoning]
        }
    
    def analyze_email(self, email):
        """
        Analyze a single email through the multi-agent workflow
        
        Args:
            email (dict): Email object
            
        Returns:
            dict: Complete analysis with all agent results and final decision
        """
        # Initialize state
        initial_state = {
            "email": email,
            "document_analysis": {},
            "classification": {},
            "spam_analysis": {},
            "unwanted_analysis": {},
            "final_decision": "",
            "confidence": "",
            "reasoning_chain": []
        }
        
        # Run through the workflow
        final_state = self.app.invoke(initial_state)
        
        return final_state
    
    def batch_analyze(self, emails):
        """
        Analyze multiple emails through the multi-agent workflow
        
        Args:
            emails (list): List of email objects
            
        Returns:
            dict: Results grouped by final decision
        """
        results = {
            'preserve': [],
            'delete': [],
            'review': []
        }
        
        print(f"\n🔄 Running multi-agent analysis on {len(emails)} emails...\n")
        
        for i, email in enumerate(emails, 1):
            # Analyze through workflow
            analysis = self.analyze_email(email)
            
            # Store result
            email_info = {
                'email': email,
                'analysis': analysis
            }
            
            decision = analysis['final_decision']
            results[decision].append(email_info)
            
            # Display progress
            subject = email.get('subject', 'No Subject')[:60]
            icon_map = {'preserve': '🛡️', 'delete': '🗑️', 'review': '👁️'}
            icon = icon_map.get(decision, '❓')
            
            print(f"{i}. {icon} {decision.upper()} - {subject}")
            print(f"   Confidence: {analysis['confidence']}")
            print(f"   Reasoning Chain:")
            for reasoning in analysis['reasoning_chain']:
                print(f"      • {reasoning}")
            print()
        
        return results


# Test the orchestrator
if __name__ == "__main__":
    print("="*100)
    print("🎭 MULTI-AGENT ORCHESTRATOR - Test with LangGraph")
    print("="*100 + "\n")
    
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # Test emails covering different scenarios
    test_emails = [
        {
            'subject': 'PAYSLIP - March 2024',
            'from': {'emailAddress': {'address': 'payroll@company.com', 'name': 'Payroll'}},
            'bodyPreview': 'Your payslip for March is attached.',
            'receivedDateTime': (today - timedelta(days=30)).isoformat(),
            'isRead': True,
            'hasAttachments': True
        },
        {
            'subject': 'Weekly Newsletter - Tech Updates',
            'from': {'emailAddress': {'address': 'news@techcrunch.com', 'name': 'TechCrunch'}},
            'bodyPreview': 'Top stories this week. Unsubscribe anytime.',
            'receivedDateTime': (today - timedelta(days=1000)).isoformat(),  # Old
            'isRead': False
        },
        {
            'subject': 'URGENT: Account verification required',
            'from': {'emailAddress': {'address': 'security@paypa1.com', 'name': 'PayPal'}},
            'bodyPreview': 'Your account will be suspended. Click here now!',
            'receivedDateTime': (today - timedelta(days=2)).isoformat(),
            'isRead': False
        },
        {
            'subject': 'Meeting tomorrow at 2pm',
            'from': {'emailAddress': {'address': 'colleague@work.com', 'name': 'Sarah'}},
            'bodyPreview': 'Can we discuss the project? See you tomorrow.',
            'receivedDateTime': (today - timedelta(days=1)).isoformat(),
            'isRead': True
        },
        {
            'subject': 'Your O2 bill is ready',
            'from': {'emailAddress': {'address': 'billing@o2.co.uk', 'name': 'O2'}},
            'bodyPreview': 'Your latest bill is available.',
            'receivedDateTime': (today - timedelta(days=15)).isoformat(),
            'isRead': True
        }
    ]
    
    # Create orchestrator and analyze
    orchestrator = MultiAgentOrchestrator()
    results = orchestrator.batch_analyze(test_emails)
    
    # Summary
    print("\n" + "="*100)
    print("📊 MULTI-AGENT ANALYSIS SUMMARY")
    print("="*100)
    print(f"🛡️ PRESERVE: {len(results['preserve'])} emails")
    print(f"🗑️ DELETE: {len(results['delete'])} emails")
    print(f"👁️ REVIEW: {len(results['review'])} emails")
    print("="*100 + "\n")