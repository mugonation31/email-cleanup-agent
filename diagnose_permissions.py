"""
Diagnose Azure AD App Permissions
"""
import msal
import requests
import json
from config.settings import CLIENT_ID, TENANT_ID

print("="*100)
print("🔍 AZURE AD APP PERMISSIONS DIAGNOSTIC")
print("="*100 + "\n")

print(f"App Client ID: {CLIENT_ID}")
print(f"Tenant ID: {TENANT_ID}\n")

# Load cached token
cache = msal.SerializableTokenCache()
try:
    with open('token_cache.bin', 'r') as f:
        cache.deserialize(f.read())
    print("✅ Token cache loaded\n")
except:
    print("❌ No token cache found - please authenticate first\n")
    exit(1)

# Get account
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}',
    token_cache=cache
)

accounts = app.get_accounts()
if not accounts:
    print("❌ No accounts in cache\n")
    exit(1)

print(f"✅ Authenticated as: {accounts[0].get('username')}\n")

# Get token
scopes = [
    'https://graph.microsoft.com/Mail.ReadWrite',
    'https://graph.microsoft.com/Mail.Send',
    'https://graph.microsoft.com/User.Read'
]

result = app.acquire_token_silent(scopes, account=accounts[0])

if 'access_token' not in result:
    print("❌ Failed to get token\n")
    exit(1)

token = result['access_token']

# Decode token to see what scopes we actually have
import base64
parts = token.split('.')
if len(parts) >= 2:
    # Add padding if needed
    payload = parts[1]
    payload += '=' * (4 - len(payload) % 4)

    try:
        decoded = json.loads(base64.b64decode(payload))

        print("="*100)
        print("📋 TOKEN INFORMATION")
        print("="*100)
        print(f"Audience: {decoded.get('aud', 'N/A')}")
        print(f"Issuer: {decoded.get('iss', 'N/A')}")
        print(f"App ID: {decoded.get('appid', 'N/A')}")
        print(f"User: {decoded.get('unique_name', 'N/A')}")

        # Check scopes
        scopes_in_token = decoded.get('scp', '')
        print(f"\n🔑 SCOPES IN TOKEN:")
        if scopes_in_token:
            for scope in scopes_in_token.split(' '):
                print(f"   ✅ {scope}")
        else:
            print("   ❌ NO SCOPES FOUND!")

        # Check if we have the right scopes
        print(f"\n🎯 REQUIRED SCOPES CHECK:")
        required = ['Mail.ReadWrite', 'Mail.Send', 'User.Read']
        for req in required:
            if req in scopes_in_token:
                print(f"   ✅ {req} - FOUND")
            else:
                print(f"   ❌ {req} - MISSING!")

    except Exception as e:
        print(f"⚠️ Couldn't decode token: {e}")

print(f"\n{'='*100}")
print("🧪 API PERMISSION TESTS")
print("="*100 + "\n")

headers = {'Authorization': f'Bearer {token}'}

tests = [
    {
        'name': 'Read User Profile',
        'url': 'https://graph.microsoft.com/v1.0/me',
        'required_scope': 'User.Read',
        'description': 'Basic user information'
    },
    {
        'name': 'List Messages',
        'url': 'https://graph.microsoft.com/v1.0/me/messages',
        'params': {'$top': '1'},
        'required_scope': 'Mail.ReadWrite or Mail.Read',
        'description': 'Read user email messages'
    },
    {
        'name': 'List Mail Folders',
        'url': 'https://graph.microsoft.com/v1.0/me/mailFolders',
        'required_scope': 'Mail.ReadWrite or Mail.Read',
        'description': 'Read mail folder structure'
    },
    {
        'name': 'Get Inbox',
        'url': 'https://graph.microsoft.com/v1.0/me/mailFolders/inbox',
        'required_scope': 'Mail.ReadWrite or Mail.Read',
        'description': 'Access inbox folder'
    },
]

passed = 0
failed = 0

for i, test in enumerate(tests, 1):
    print(f"{i}. {test['name']}")
    print(f"   Required Scope: {test['required_scope']}")
    print(f"   Description: {test['description']}")

    try:
        r = requests.get(test['url'], headers=headers, params=test.get('params', {}))

        if r.status_code == 200:
            print(f"   ✅ SUCCESS (Status: {r.status_code})")
            passed += 1
        elif r.status_code == 401:
            print(f"   ❌ UNAUTHORIZED (Status: {r.status_code})")
            print(f"   ⚠️  This scope is NOT granted or needs admin consent!")
            failed += 1
        elif r.status_code == 403:
            print(f"   ❌ FORBIDDEN (Status: {r.status_code})")
            print(f"   ⚠️  Permission denied - check API permissions in Azure AD!")
            failed += 1
        else:
            print(f"   ⚠️  UNEXPECTED STATUS: {r.status_code}")
            failed += 1

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        failed += 1

    print()

print("="*100)
print(f"📊 RESULTS: {passed} passed, {failed} failed")
print("="*100 + "\n")

if failed > 0:
    print("🚨 ACTION REQUIRED:")
    print("="*100)
    print("Your Azure AD app registration is missing the required permissions.")
    print()
    print("📝 STEPS TO FIX:")
    print("1. Go to: https://portal.azure.com")
    print("2. Navigate to: Azure Active Directory → App Registrations")
    print(f"3. Find your app: {CLIENT_ID}")
    print("4. Click: API Permissions (left sidebar)")
    print("5. Click: Add a permission → Microsoft Graph → Delegated permissions")
    print("6. Add these permissions:")
    print("   - Mail.Read")
    print("   - Mail.ReadWrite")
    print("   - Mail.Send")
    print("   - User.Read")
    print("7. Click: Grant admin consent for [Your Organization]")
    print("8. Wait 2-5 minutes for changes to propagate")
    print("9. Delete token_cache.bin and re-authenticate")
    print("="*100)
else:
    print("✅ All permissions are working correctly!")
