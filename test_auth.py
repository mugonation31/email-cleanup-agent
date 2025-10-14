"""
Quick authentication test to debug 401 issues
"""
import msal
import requests
from config.settings import CLIENT_ID, CLIENT_SECRET, TENANT_ID

print("="*100)
print("🔍 AUTHENTICATION DEBUG TEST")
print("="*100 + "\n")

print(f"Client ID: {CLIENT_ID}")
print(f"Tenant ID: {TENANT_ID}")
print(f"Has Client Secret: {bool(CLIENT_SECRET)}\n")

# Initialize MSAL app
app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET,
)

scopes = [
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read"
]

print("🔐 Starting device code flow...\n")

# Initiate device flow
flow = app.initiate_device_flow(scopes=scopes)

if "user_code" not in flow:
    print("❌ Failed to create device flow")
    print(f"Error: {flow}")
    exit(1)

print(flow["message"])
print("\n⏳ Waiting for authentication...\n")

# Complete device flow
result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    print("❌ Authentication failed!")
    print(f"Error: {result.get('error')}")
    print(f"Description: {result.get('error_description')}")
    exit(1)

token = result["access_token"]
print("✅ Token acquired successfully!\n")
print(f"Token (first 50 chars): {token[:50]}...\n")

# Test 1: Get user profile
print("="*100)
print("TEST 1: Get User Profile (/me)")
print("="*100)

headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"✅ User: {user.get('displayName')} <{user.get('mail')}>")
else:
    print(f"❌ Error: {response.text}")

print()

# Test 2: Get mailbox folders
print("="*100)
print("TEST 2: Get Mail Folders (/me/mailFolders)")
print("="*100)

response = requests.get("https://graph.microsoft.com/v1.0/me/mailFolders", headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    folders = response.json()
    print(f"✅ Found {len(folders.get('value', []))} folders")
    for folder in folders.get('value', [])[:5]:
        print(f"   - {folder['displayName']}")
else:
    print(f"❌ Error: {response.text}")

print()

# Test 3: Get inbox messages (the failing call)
print("="*100)
print("TEST 3: Get Inbox Messages (/me/mailFolders/inbox/messages)")
print("="*100)

url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
params = {
    "$select": "id,subject,from",
    "$top": 5
}

response = requests.get(url, headers=headers, params=params)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    messages = response.json()
    print(f"✅ Found {len(messages.get('value', []))} messages")
    for msg in messages.get('value', []):
        print(f"   - {msg.get('subject', 'No subject')[:50]}")
else:
    print(f"❌ Error: {response.text}")

print()

# Test 4: Get inbox messages with inferenceClassification filter (your exact failing call)
print("="*100)
print("TEST 4: Get OTHER Inbox Messages (with filter)")
print("="*100)

url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
params = {
    "$select": "id,subject,from,receivedDateTime,hasAttachments,bodyPreview",
    "$top": 5,
    "$filter": "inferenceClassification eq 'other'"
}

response = requests.get(url, headers=headers, params=params)

print(f"Status: {response.status_code}")
print(f"URL: {response.url}")
if response.status_code == 200:
    messages = response.json()
    print(f"✅ Found {len(messages.get('value', []))} messages")
    for msg in messages.get('value', []):
        print(f"   - {msg.get('subject', 'No subject')[:50]}")
else:
    print(f"❌ Error Response:")
    print(f"   Status: {response.status_code}")
    print(f"   Body: {response.text}")
    print(f"\n💡 This is the exact error you're seeing!")

print("\n" + "="*100)
print("🏁 TEST COMPLETE")
print("="*100)
