"""Amazon SES email delivery helpers."""

from __future__ import annotations

import json
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class EmailDeliveryError(RuntimeError):
    """Raised when an email cannot be submitted to Amazon SES."""


def send_password_reset_template(
    *,
    recipient_email: str,
    recipient_name: str | None,
    reset_code: str,
    expiry_minutes: int,
) -> str:
    """Send the stored Amazon SES password-reset template.

    Returns the SES MessageId when the message is accepted.
    """

    region = os.getenv("AWS_REGION", "ap-south-1")
    sender_email = os.getenv("SES_FROM_EMAIL")
    template_name = os.getenv(
        "SES_PASSWORD_RESET_TEMPLATE",
        "PortfolioPasswordReset",
    )

    if not sender_email:
        raise EmailDeliveryError(
            "SES_FROM_EMAIL environment variable is not configured"
        )

    template_data = {
        "name": recipient_name or "Investor",
        "reset_code": str(reset_code),
        "expiry_minutes": str(expiry_minutes),
    }

    try:
        ses_client = boto3.client("sesv2", region_name=region)

        response = ses_client.send_email(
            FromEmailAddress=sender_email,
            Destination={
                "ToAddresses": [recipient_email],
            },
            Content={
                "Template": {
                    "TemplateName": template_name,
                    "TemplateData": json.dumps(template_data),
                }
            },
        )
    except (BotoCoreError, ClientError) as exc:
        raise EmailDeliveryError(
            "Amazon SES could not send the password-reset email"
        ) from exc

    message_id = response.get("MessageId")

    if not message_id:
        raise EmailDeliveryError(
            "Amazon SES accepted the request without returning a MessageId"
        )

    return message_id