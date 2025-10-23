from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager

CHAT_ID = CredentialsManager.get_parameter("TELEGRAM_CHAT_ID")

EMAIL_SUBJECT = "Test email"

EMAIL_BODY = "This is a test email"

TELEGRAM_BODY = "CodeMie Test Message"

EMAIL_TOOL_PROMPT = f"""
    Write an email to the 'codemieautomation@gmail.com' with the following information:
        - Subject: '{EMAIL_SUBJECT}'
        - Body: '{EMAIL_BODY}'
"""

EMAIL_RESPONSE = f"The email has been sent successfully to codemieautomation@gmail.com with the subject '{EMAIL_SUBJECT}' and the body '{EMAIL_BODY}'."

TELEGRAM_TOOL_PROMPT = f"Send message to chat_id {CHAT_ID} with text '{TELEGRAM_BODY}'"

TELEGRAM_RESPONSE = (
    f"The message '{TELEGRAM_BODY}' has been successfully sent to chat_id {CHAT_ID}."
)
