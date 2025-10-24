from codemie_test_harness.tests.enums.environment import Environment
from codemie_test_harness.tests.utils.env_resolver import get_environment

import pytest

from codemie_test_harness.tests.enums.tools import NotificationTool
from codemie_test_harness.tests.test_data.notification_tools_test_data import (
    EMAIL_SUBJECT,
    EMAIL_BODY,
    EMAIL_RESPONSE,
)

notification_tools_test_data = [
    pytest.param(
        NotificationTool.EMAIL,
        {
            "recipient_emails": ["codemieautomation@gmail.com"],
            "subject": f"{EMAIL_SUBJECT}",
            "body": f"{EMAIL_BODY}",
        },
        EMAIL_RESPONSE,
        marks=[
            pytest.mark.email,
            pytest.mark.skipif(
                get_environment() in [Environment.LOCALHOST, Environment.GCP],
                reason="Skipping this test on local environment",
            ),
        ],
        id=NotificationTool.EMAIL,
    ),
    pytest.param(
        NotificationTool.TELEGRAM,
        {
            "method": "POST",
            "relative_url": "sendMessage",
            "params": '{"chat_id": "7896103913", "text": "CodeMie Test Message"}',
        },
        {
            "ok": "true",
            "result": {
                "message_id": 511,
                "from": {
                    "id": 7647598607,
                    "is_bot": "true",
                    "first_name": "codeMieTestBot",
                    "username": "codemietest_bot",
                },
                "chat": {
                    "id": 7896103913,
                    "first_name": "Babun",
                    "username": "babun20",
                    "type": "private",
                },
                "date": 1753959598,
                "text": "CodeMie Test Message",
            },
        },
        marks=pytest.mark.telegram,
        id=NotificationTool.TELEGRAM,
    ),
]
