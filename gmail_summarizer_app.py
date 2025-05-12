from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import streamlit as st
from openai import OpenAI
import os



SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# === Utility Functions ===
def extract_text_from_html(html):
    """Extracts text from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

# === Gmail API Authentication ===
@st.cache_resource
def gmail_login():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('gmail', 'v1', credentials=creds)

def fetch_gmail_messages(service, max_results=10):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    email_data = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()

        headers = msg_detail['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        from_address = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        parts = msg_detail['payload'].get('parts', [])
        body_data = ''
        for part in parts:
            if part.get('mimeType') == 'text/html':
                body_data = part['body'].get('data', '')
                break

        if body_data:
            import base64
            import html
            decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            body_text = extract_text_from_html(html.unescape(decoded_body))
        else:
            body_text = '(No content)'

        email_data.append({
            'subject': subject,
            'from': from_address,
            'received': date,
            'bodyText': body_text
        })

    return email_data

# === OpenAI API Setup ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_email(email):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize this email: {email}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# === Streamlit App ===
st.title("Gmail Email Summarizer")

if st.button("Summarize Gmail Inbox"):
    with st.spinner('Logging in and fetching emails...'):
        service = gmail_login()
        email_data = fetch_gmail_messages(service)

        if email_data:
            st.subheader("📬 Summarized Emails")

            for email in email_data:
                received = email.get('received')
                subject = email.get('subject', '(no subject)')
                from_address = email.get('from', '(unknown sender)')
                body = email.get('bodyText', '(no content)')
                summary = summarize_email(body)
                formatted_summary = summary.strip().replace('\n', '\n> ')
                st.markdown(f"""
                            **📌 Subject:** {subject}\n
                            *✉️ From:* `{from_address}`\n
                            *📅 Received:* `{received}`\n

                            **📝 Summary:**
                            > {formatted_summary}
                            """)

        else:
            st.warning("No emails found.")
        st.success("Emails fetched successfully!")
        st.balloons()
