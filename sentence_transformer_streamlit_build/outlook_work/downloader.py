# downloader_local.py
import os
import streamlit as st
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# -------------------------------
# CV Folder Fetcher
# -------------------------------
class CVFolderFetcher:
    def __init__(self, folder_path, parser=None, analyzer=None):
        self.folder_path = folder_path
        self.parser = parser
        self.analyzer = analyzer
        os.makedirs(self.folder_path, exist_ok=True)

    def process_jobbox(self):
        """Process all CVs in the given local folder"""
        print(f"📂 Checking folder: {self.folder_path}")
        files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(".pdf")]

        if not files:
            print("⚠️ No CVs found in the folder.")
            return 0

        for file in files:
            try:
                file_path = os.path.join(self.folder_path, file)
                print(f"✅ Found CV: {file_path}")

                if self.parser:
                    try:
                        parsed_data = self.parser.parse(file_path)
                        if parsed_data is not None:
                            print(f"📄 Parsed: {parsed_data}")
                        else:
                            print(f"⚠️ Parse returned None for: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Parse failed: {e}")
            except Exception as e:
                print(f"❌ Error processing file {file}: {e}")
        return len(files)

# -------------------------------
# SMTP Email Sender
# -------------------------------
class EmailSenderSMTP:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email(self, recipient_email, subject, body, attachment_path=None):
        """Send email using SMTP"""
        if not recipient_email or not subject or not body:
            st.error("Missing required email fields")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            return True
        except Exception as e:
            st.error(f"Error sending email to {recipient_email}: {str(e)}")
            return False

# -------------------------------
# Bulk Email Sender
# -------------------------------
def send_bulk_emails(top_candidates_df, email_template, smtp_config):
    """
    Send emails to top candidates via SMTP (no Outlook required)
    """
    successful_emails = []

    if top_candidates_df is None or top_candidates_df.empty:
        st.error("No candidates data provided")
        return successful_emails

    if not email_template or not smtp_config:
        st.error("Missing email template or SMTP config")
        return successful_emails

    sender = EmailSenderSMTP(
        smtp_server=smtp_config["server"],
        smtp_port=smtp_config["port"],
        sender_email=smtp_config["email"],
        sender_password=smtp_config["password"],
    )

    for index, candidate in top_candidates_df.iterrows():
        try:
            candidate_name = candidate.get("Name", "Candidate")
            position = candidate.get("Position", "the position")
            candidate_email = candidate.get("Email")

            if not candidate_email or pd.isna(candidate_email):
                print(f"⚠️ Skipping candidate {candidate_name} - no email address")
                continue

            personalized_body = email_template["body"].format(
                candidate_name=candidate_name,
                position=position,
                company_name="Bitskraft",
            )
            personalized_subject = email_template["subject"].format(position=position)

            success = sender.send_email(
                recipient_email=candidate_email,
                subject=personalized_subject,
                body=personalized_body,
            )

            if success:
                successful_emails.append(candidate_email)
                print(f"✅ Email sent to: {candidate_email}")
                time.sleep(1)
            else:
                print(f"❌ Failed to send email to: {candidate_email}")

        except Exception as e:
            print(f"❌ Error processing candidate {index}: {e}")
            continue

    return successful_emails

# -------------------------------
# Default Email Template
# -------------------------------
DEFAULT_EMAIL_TEMPLATE = {
    "subject": "Congratulations! Next Steps for {position} Position at Bitskraft",
    "body": """Dear {candidate_name},

We are impressed with your qualifications and would like to invite you to the next stage of our hiring process for the {position} position at {company_name}.

Your application stood out among many others, and we believe your skills and experience would be a valuable addition to our team.

Next Steps:
1. We will contact you within 2 business days to schedule an interview
2. Please be prepared to discuss your experience in more detail
3. We may conduct a technical assessment based on the role requirements

If you have any questions in the meantime, please don't hesitate to reach out.

Best regards,
The Bitskraft Hiring Team"""
}
