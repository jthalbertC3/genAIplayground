import streamlit as st
import msal
import requests
import os
from bs4 import BeautifulSoup

# === Configuration ===
CLIENT_ID = '6aecb347-917b-4309-9fbb-58603f4905c8'
TENANT_ID = '53ad779a-93e7-485c-ba20-ac8290d7252b'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ["Mail.Read", "Calendars.Read"]
CACHE_FILE = 'token_cache.bin'

# === Token Caching ===
cache = msal.SerializableTokenCache()
if os.path.exists(CACHE_FILE):
    cache.deserialize(open(CACHE_FILE, 'r').read())

app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    token_cache=cache
)

# === Utility Functions ===
def extract_text_from_html(html):
    """Extracts text from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

# === Streamlit App ===
st.title("Outlook Email Summarizer")
st.write("Click the button below to fetch and summarize your latest emails.")

if st.button("Summarize My Inbox"):
    with st.spinner('Fetching and summarizing emails...'):
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
        else:
            flow = app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                st.error("Failed to create device flow")
                st.stop()

            st.info(f"🔐 Please go to [Microsoft Device Login](https://microsoft.com/devicelogin) and enter the code: {flow['user_code']}")
	    
            result = app.acquire_token_by_device_flow(flow)

        if 'access_token' in result:
            access_token = result['access_token']
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            endpoint = 'https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages'
            response = requests.get(endpoint, headers=headers)

            if response.status_code == 200:
                messages = response.json().get('value', [])
                email_data = []
                for msg in messages:
                    email_data.append({
                        "subject": msg.get('subject'),
                        "from": msg.get('from', {}).get('emailAddress', {}).get('address'),
                        "received": msg.get('receivedDateTime'),
                        "bodyPreview": msg.get('bodyPreview'),
                        "bodyHTML": msg.get('body', {}).get('content'),
                        "bodyText": extract_text_from_html(msg.get('body', {}).get('content', '(no content)'))
                    })

                # Simulate API call to summarize and extract to-dos
                def mock_api_call(emails):
                    summary = "Summary of your latest emails."
                    for email in emails:
                        received = email.get('received')
                        subject = email.get('subject', '(no subject)')
                        from_address = email.get('from', '(unknown sender)')
                        body = email.get('bodyText', '(no content)')
                        summary += f"\n- {subject} from {from_address} on {received}: {body}"

                    return summary

                summary = mock_api_call(email_data)

                st.subheader("Summary")
                st.write(summary)


            else:
                st.error(f"Error fetching emails: {response.status_code}")
                st.write(response.text)
        else:
            st.error("Failed to acquire token.")
            st.write(result.get("error_description"))

        # Save cache
        if cache.has_state_changed:
            with open(CACHE_FILE, 'w') as f:
                f.write(cache.serialize())

