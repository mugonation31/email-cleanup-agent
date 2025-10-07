import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Microsoft Graph API settings
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# API endpoints
# For apps that support both work and personal accounts
AUTHORITY = 'https://login.microsoftonline.com/common'
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

# Scopes for Microsoft Graph API
SCOPES = ['https://graph.microsoft.com/.default']

# OpenAI API settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# VIP Email Addresses (always preserve)
VIP_EMAILS_RAW = os.getenv('VIP_EMAILS', '')
VIP_EMAILS = [email.strip().lower() for email in VIP_EMAILS_RAW.split(',') if email.strip()]

def validate_config():
    """Check if all required environment variables are set"""
    required = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID', 'OPENAI_API_KEY']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"❌ Missing environment variables: {', '.join(missing)}")
    
    print("✅ Configuration validated successfully!")

     # Show VIP emails (for verification)
    if VIP_EMAILS:
        print(f"🔒 VIP Emails loaded: {len(VIP_EMAILS)} addresses protected")
    
    return True

if __name__ == "__main__":
    validate_config()