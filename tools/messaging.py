import imaplib
import email
from email.header import decode_header
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from config import Config

logger = logging.getLogger(__name__)

class MessagingTools:
    def __init__(self):
        self.email_address = Config.EMAIL_ADDRESS
        self.email_password = Config.EMAIL_PASSWORD
        self.imap_server = Config.EMAIL_IMAP_SERVER
        self.imap_port = Config.EMAIL_IMAP_PORT

    def check_emails(self, limit=5):
        """Fetches and summarizes unread emails."""
        if not self.email_address or not self.email_password:
            return "Email credentials are not set. I'm not a hacker, I need a password! 🔐"

        try:
            # Connect to the server
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_address, self.email_password)

            # Select the inbox
            status, messages = imap.select("INBOX")

            # Search for unread emails
            status, response = imap.search(None, "UNSEEN")
            email_ids = response[0].split()

            if not email_ids:
                return "No unread emails. You're popular, but not *that* popular today. 😉"

            # Get the latest `limit` emails
            latest_email_ids = email_ids[-limit:]
            summary = f"You have {len(email_ids)} unread emails. Here are the latest {len(latest_email_ids)}:\n"

            for eid in latest_email_ids:
                res, msg_data = imap.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        from_ = msg.get("From")
                        summary += f"- From: {from_} | Subject: {subject}\n"

            imap.close()
            imap.logout()
            return summary

        except Exception as e:
            logger.error(f"Email error: {e}")
            return f"I couldn't check your emails. Error: {e}"

    def send_whatsapp(self, phone_no, message):
        """
        Sends a WhatsApp message using Headless Selenium.
        """
        try:
            options = Options()
            profile_dir = os.path.join(Config.BASE_DIR, "wa_profile")
            options.add_argument(f"user-data-dir={profile_dir}")
            # Ensure headless is handled correctly.
            # Note: WhatsApp Web might block headless without user-agent and window-size
            options.add_argument("--headless=new")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1920,1080")

            driver = webdriver.Chrome(options=options)
            driver.get(f"https://web.whatsapp.com/send?phone={phone_no}&text={message}")

            # Wait for the chat to load.
            # We look for the message input box or the send button.
            # The send button usually has a specific aria-label or icon.
            # Using WebDriverWait is safer than sleep.
            wait = WebDriverWait(driver, 60) # Long wait for initial load/QR

            # Wait for send button to be clickable.
            # Note: Selectors are tricky and change.
            # A common strategy is waiting for the message input to be present (which means we are logged in)
            # and then pressing Enter.

            # Wait for content to load
            try:
                # Wait until the 'loading' screen is gone or specific element appears
                wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]')))
                logger.info("WhatsApp loaded.")
            except:
                driver.quit()
                return "WhatsApp timed out. Did you scan the QR code yet? (Run without headless first!)"

            # Focus input and send
            action = webdriver.ActionChains(driver)
            action.send_keys(Keys.ENTER)
            action.perform()

            time.sleep(5) # Allow send animation
            driver.quit()
            return f"Message sent to {phone_no}. (Hopefully!)"

        except Exception as e:
            logger.error(f"WhatsApp error: {e}")
            return f"Couldn't send WhatsApp message. Maybe Mark Zuckerberg is watching? 👀 Error: {e}"
