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

def validate_config():
    """Check if all required environment variables are set"""
    required = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"❌ Missing environment variables: {', '.join(missing)}")
    
    print("✅ Configuration validated successfully!")
    return True

if __name__ == "__main__":
    validate_config()