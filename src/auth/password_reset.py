"""Password-reset email delivery through Amazon SES SMTP."""

import os
import smtplib
from email.message import EmailMessage

from src.database.db import create_password_reset_code, generate_password_reset_code


GENERIC_RESPONSE = (
    "If the account details match, a reset code has been sent. "
    "The code expires shortly."
)


def request_password_reset(username: str, email: str) -> None:
    """Create and email a reset code without revealing account existence."""
    code = generate_password_reset_code()
    ttl_minutes = int(os.environ.get("PASSWORD_RESET_CODE_TTL_MINUTES", "15"))
    created = create_password_reset_code(username, email, code, ttl_minutes)
    if not created:
        return

    message = EmailMessage()
    message["Subject"] = "AXIOM password reset code"
    message["From"] = os.environ["SMTP_FROM_EMAIL"]
    message["To"] = email.strip()
    message.set_content(
        f"Your AXIOM password reset code is: {code}\n\n"
        f"It expires in {ttl_minutes} minutes. If you did not request this, "
        "you can ignore this email."
    )

    with smtplib.SMTP(
        os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=20
    ) as smtp:
        smtp.starttls()
        smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)
