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
    
    def get_emails(self, limit=10):
        """Fetch emails from inbox"""
        if not self.access_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        print(f"\n📧 Fetching {limit} emails from your inbox...")
        
        # Graph API endpoint for messages
        endpoint = f"{GRAPH_API_ENDPOINT}/me/messages"
        
        # Parameters
        params = {
            '$top': limit,
            '$select': 'id,subject,from,receivedDateTime,hasAttachments,bodyPreview',
            '$orderby': 'receivedDateTime DESC'
        }
        
        # Headers
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔍 DEBUG - Request URL: {endpoint}")
        print(f"🔍 DEBUG - Request params: {params}")
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            emails = response.json().get('value', [])
            print(f"✅ Successfully fetched {len(emails)} emails!")
            return emails
            
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Show response headers for debugging
            print(f"\n🔍 DEBUG - Response Headers:")
            for key, value in response.headers.items():
                print(f"   {key}: {value}")
            
            # Try to parse error details
            try:
                error_details = response.json()
                print(f"\n🔍 DEBUG - Error Details:")
                print(f"   {error_details}")
            except:
                print("   (Could not parse error as JSON)")
            
            return None
            
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return None
    
    def display_emails(self, emails):
        """Pretty print email list"""
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
            
            print(f"{i}. {has_attachments} {subject}")
            print(f"   👤 From: {sender_name} <{sender_email}>")
            print(f"   📅 Date: {date}")
            print(f"   💬 Preview: {preview}")
            print("-" * 100)
        
        print("\n🎉 Connection successful! Your email agent is working!\n")

# Test the connector
if __name__ == "__main__":
    print("="*100)
    print("🚀 EMAIL CLEANUP AGENT - Connection Test")
    print("="*100 + "\n")
    
    connector = OutlookConnector()
    
    if connector.authenticate():
        emails = connector.get_emails(limit=10)
        if emails:
            connector.display_emails(emails)
            
            # Show stats
            print("📊 Quick Stats:")
            print(f"   Total emails fetched: {len(emails)}")
            print(f"   Emails with attachments: {sum(1 for e in emails if e.get('hasAttachments'))}")
            print("\n✅ Setup complete! Ready to build the cleanup agents!\n")