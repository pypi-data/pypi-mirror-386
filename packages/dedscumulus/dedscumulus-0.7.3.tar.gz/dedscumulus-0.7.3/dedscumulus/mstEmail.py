import msal
import requests


class graph_emailer:
    def __init__(self, client_id, client_secret, tenant_id, sender):
        # Azure AD App details
        CLIENT_ID = client_id
        CLIENT_SECRET = client_secret
        TENANT_ID = tenant_id
        AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
        SCOPES = ["https://graph.microsoft.com/.default"]

        # Create MSAL app
        app = msal.ConfidentialClientApplication(
            CLIENT_ID, 
            authority=AUTHORITY, 
            client_credential=CLIENT_SECRET
        )

        # Get token
        result = app.acquire_token_for_client(SCOPES)
        self.access_token = result.get("access_token")

        self.sender = sender

    def send_email(self, logger, subject, content_type, body, to_field, cc_field=None, bcc_field=None, priority="normal"):
        try:
            def parse_recipients(field):
                if not field:
                    return []
                # Split by comma and strip spaces
                return [{"emailAddress": {"address": addr.strip()}} for addr in field.split(",") if addr.strip()]

            to_recipients = parse_recipients(to_field)
            cc_recipients = parse_recipients(cc_field)
            bcc_recipients = parse_recipients(bcc_field)

            # Send email via Microsoft Graph
            endpoint = f"https://graph.microsoft.com/v1.0/users/{self.sender}/sendMail"
            email_msg = {
                "message": {
                    "subject": f"{subject}",
                    "body": {
                        "contentType": f"{content_type}",
                        "content": f"{body}"
                    },
                    "toRecipients": to_recipients,
                    "importance": priority
                }
            }

            if cc_recipients:
                email_msg["message"]["ccRecipients"] = cc_recipients
            if bcc_recipients:
                email_msg["message"]["bccRecipients"] = bcc_recipients

            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            response = requests.post(endpoint, headers=headers, json=email_msg)

            if response.status_code == 202:
                logger.debug(f"send_email successful!")
                return 0
            else:
                logger.error(f"send_email failed: {response.status_code}, {response.text}")
                return -1
        except Exception as e:
            logger.error(f"send_email failed: {e}")
            return -1