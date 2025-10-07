import msal
import requests
from config.settings import (
    CLIENT_ID, 
    CLIENT_SECRET, 
    AUTHORITY, 
    GRAPH_API_ENDPOINT, 
    SCOPES
)

class OutlookConnector:
    """Connects to Microsoft Outlook via Graph API"""
    
    def __init__(self):
        self.access_token = None
        self.app = None
        
    def authenticate(self):
        """Authenticate with Microsoft Graph API using device code flow"""
        print("🔐 Authenticating with Microsoft Graph API...")
        print("📱 You'll need to sign in with your Microsoft account\n")
        
        # Create MSAL PublicClientApplication for device code flow
        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
        )
        
        # Use full scope URLs for clarity
        scopes = [
            "https://graph.microsoft.com/Mail.ReadWrite",
            "https://graph.microsoft.com/Mail.Send", 
            "https://graph.microsoft.com/User.Read"
        ]
        
        # Initiate device flow with delegated scopes
        flow = self.app.initiate_device_flow(scopes=scopes)
        
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow. Check your app registration.")
        
        # Display instructions to user
        print(flow["message"])
        print("\n⏳ Waiting for you to complete sign-in...")
        
        # Wait for user to authenticate
        result = self.app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self.access_token = result['access_token']
            print("\n✅ Authentication successful!")
            
            # DEBUG: Show what scopes we actually got
            if "scope" in result:
                print(f"🔍 DEBUG - Scopes in token: {result['scope']}")
            else:
                print("⚠️ WARNING: No scopes in token result")
            
            # DEBUG: Show token info (first 20 chars only for security)
            print(f"🔍 DEBUG - Token preview: {self.access_token[:20]}...")
            
            return True
        else:
            print(f"\n❌ Authentication failed!")
            print(f"Error: {result.get('error')}")
            print(f"Description: {result.get('error_description')}")
            return False
    
    def get_inbox_stats(self):
        """Get counts for Focused and Other inboxes"""
        if not self.access_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        print("\n📊 Analyzing your inbox breakdown...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get Focused inbox count
            focused_url = f"{GRAPH_API_ENDPOINT}/me/mailFolders/inbox/messages?$filter=inferenceClassification eq 'focused'&$count=true&$top=1"
            focused_response = requests.get(focused_url, headers=headers)
            focused_response.raise_for_status()
            
            # Get Other inbox count
            other_url = f"{GRAPH_API_ENDPOINT}/me/mailFolders/inbox/messages?$filter=inferenceClassification eq 'other'&$count=true&$top=1"
            other_response = requests.get(other_url, headers=headers)
            other_response.raise_for_status()
            
            focused_count = focused_response.json().get('@odata.count', 0)
            other_count = other_response.json().get('@odata.count', 0)
            total_count = focused_count + other_count
            
            print("\n" + "="*100)
            print("📊 INBOX BREAKDOWN")
            print("="*100)
            print(f"   🎯 Focused: {focused_count:,} emails (important)")
            print(f"   📫 Other:   {other_count:,} emails (newsletters, promotions)")
            print(f"   📬 Total:   {total_count:,} emails")
            print("="*100 + "\n")
            
            return {
                'focused': focused_count,
                'other': other_count,
                'total': total_count
            }
            
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error getting inbox stats: {e}")
            print(f"Status Code: {focused_response.status_code if 'focused_response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"❌ Unexpected Error getting inbox stats: {e}")
            return None
    
    def get_emails(self, limit=10, inbox_type='both'):
        """
        Fetch emails from inbox
        
        Args:
            limit: Number of emails to fetch
            inbox_type: 'focused', 'other', or 'both' (default)
        """
        if not self.access_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use the inbox endpoint (not just /me/messages) for inferenceClassification filtering
        endpoint = f"{GRAPH_API_ENDPOINT}/me/mailFolders/inbox/messages"
        
        # Base parameters for all requests
        # Note: Don't include inferenceClassification in $select when filtering by it
        # Note: $orderby may not work with inferenceClassification filter
        base_params = {
            '$select': 'id,subject,from,receivedDateTime,hasAttachments,bodyPreview'
        }
        
        emails = []
        
        try:
            if inbox_type == 'focused':
                print(f"\n📧 Fetching {limit} emails from FOCUSED inbox...")
                params = {**base_params, '$top': limit, '$filter': "inferenceClassification eq 'focused'"}
                
                response = requests.get(endpoint, headers=headers, params=params)
                response.raise_for_status()
                emails = response.json().get('value', [])
                
                # Mark emails with inbox type for display
                for email in emails:
                    email['_inbox_type'] = 'focused'
                
            elif inbox_type == 'other':
                print(f"\n📧 Fetching {limit} emails from OTHER inbox...")
                params = {**base_params, '$top': limit, '$filter': "inferenceClassification eq 'other'"}
                
                response = requests.get(endpoint, headers=headers, params=params)
                response.raise_for_status()
                emails = response.json().get('value', [])
                
                # Mark emails with inbox type for display
                for email in emails:
                    email['_inbox_type'] = 'other'
                
            elif inbox_type == 'both':
                print(f"\n📧 Fetching {limit//2} emails from FOCUSED and {limit//2} from OTHER...")
                
                # Get from Focused
                focused_params = {**base_params, '$top': limit//2, '$filter': "inferenceClassification eq 'focused'"}
                focused_response = requests.get(endpoint, headers=headers, params=focused_params)
                focused_response.raise_for_status()
                focused_emails = focused_response.json().get('value', [])
                
                # Mark focused emails
                for email in focused_emails:
                    email['_inbox_type'] = 'focused'
                
                # Get from Other
                other_params = {**base_params, '$top': limit//2, '$filter': "inferenceClassification eq 'other'"}
                other_response = requests.get(endpoint, headers=headers, params=other_params)
                other_response.raise_for_status()
                other_emails = other_response.json().get('value', [])
                
                # Mark other emails
                for email in other_emails:
                    email['_inbox_type'] = 'other'
                
                emails = focused_emails + other_emails
            
            print(f"✅ Successfully fetched {len(emails)} emails!")
            return emails
            
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
            if 'response' in locals():
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
            return None
            
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return None
    
    def display_emails(self, emails):
        """Pretty print email list with inbox type labels"""
        if not emails:
            print("\n❌ No emails to display.")
            return
        
        print("\n" + "="*100)
        print(f"📬 YOUR INBOX - Showing {len(emails)} most recent emails")
        print("="*100 + "\n")
        
        for i, email in enumerate(emails, 1):
            # Extract sender info
            sender = email.get('from', {})
            sender_email = sender.get('emailAddress', {}).get('address', 'Unknown')
            sender_name = sender.get('emailAddress', {}).get('name', 'Unknown')
            
            # Email details
            subject = email.get('subject', 'No Subject')
            date = email.get('receivedDateTime', 'Unknown')[:10]  # Just the date
            has_attachments = "📎" if email.get('hasAttachments') else "  "
            preview = email.get('bodyPreview', '')[:80] + "..." if email.get('bodyPreview') else ""
            
            # Inbox type label
            inbox_classification = email.get('_inbox_type', 'unknown')
            inbox_label = "🎯 FOCUSED" if inbox_classification == 'focused' else "📫 OTHER"
            
            print(f"{i}. {has_attachments} [{inbox_label}] {subject}")
            print(f"   👤 From: {sender_name} <{sender_email}>")
            print(f"   📅 Date: {date}")
            print(f"   💬 Preview: {preview}")
            print("-" * 100)
        
        print("\n🎉 Connection successful! Your email agent is working!\n")

# Test the connector
if __name__ == "__main__":
    print("="*100)
    print("🚀 EMAIL CLEANUP AGENT - Connection Test with Focused/Other Options")
    print("="*100 + "\n")
    
    connector = OutlookConnector()
    
    if connector.authenticate():
        # Show inbox breakdown
        stats = connector.get_inbox_stats()
        
        # Fetch emails - you can change inbox_type to 'focused', 'other', or 'both'
        emails = connector.get_emails(limit=10, inbox_type='both')
        
        if emails:
            connector.display_emails(emails)
            
            # Show stats
            print("📊 Quick Stats:")
            print(f"   Total emails fetched: {len(emails)}")
            print(f"   Emails with attachments: {sum(1 for e in emails if e.get('hasAttachments'))}")
            
            if stats:
                print(f"\n💡 Your inbox has {stats['focused']:,} important emails and {stats['other']:,} other emails")
                print(f"   That's a {(stats['other']/stats['total']*100):.1f}% spam/newsletter rate!")
            
            print("\n✅ Setup complete! Ready to build the cleanup agents!\n")