import msal
import requests

# === 🔐 Replace these with your actual values ===
CLIENT_ID = '6aecb347-917b-4309-9fbb-58603f4905c8'
TENANT_ID = '53ad779a-93e7-485c-ba20-ac8290d7252b'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
REDIRECT_URI = 'http://localhost'
SCOPES = ["Mail.Read", "Calendars.Read"]

# === 🔑 Get Access Token ===
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY
)

flow = app.initiate_device_flow(scopes=["Mail.Read", "Calendars.Read"])
if "user_code" not in flow:
    raise Exception("Failed to create device flow")

print(f"🔐 Please go to {flow['verification_uri']} and enter the code: {flow['user_code']}")
result = app.acquire_token_by_device_flow(flow)


if 'access_token' in result:
    print("✅ Access token acquired.")
    access_token = result['access_token']

    # === 📬 Call Microsoft Graph to get emails ===
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # You can modify this to get more or fewer messages
    endpoint = 'https://graph.microsoft.com/v1.0/me/messages?$top=10'

    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        messages = response.json().get('value', [])
        for i, msg in enumerate(messages, 1):
            print(f"\n📧 Email {i}")
            print(f"Subject: {msg.get('subject')}")
            print(f"From: {msg.get('from', {}).get('emailAddress', {}).get('address')}")
            print(f"Received: {msg.get('receivedDateTime')}")
            print(f"Body Preview: {msg.get('bodyPreview')}")
    else:
        print(f"❌ Error fetching emails: {response.status_code}")
        print(response.text)
else:
    print("❌ Failed to acquire token.")
    print(result.get("error_description"))

