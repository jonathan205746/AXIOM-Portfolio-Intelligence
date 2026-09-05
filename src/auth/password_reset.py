"""Password-reset email delivery through Amazon SES templates."""

import os

from src.auth.ses_email import send_password_reset_template
from src.database.db import (
    create_password_reset_code,
    generate_password_reset_code,
)


GENERIC_RESPONSE = (
    "If the account details match, a reset code has been sent. "
    "The code expires shortly."
)


def request_password_reset(username: str, email: str) -> None:
    """Create and email a reset code without revealing account existence."""
    code = generate_password_reset_code()

    ttl_minutes = int(
        os.environ.get("PASSWORD_RESET_CODE_TTL_MINUTES", "15")
    )
    cooldown_seconds = int(
        os.environ.get("PASSWORD_RESET_RESEND_COOLDOWN_SECONDS", "60")
    )

    normalized_email = email.strip()

    created = create_password_reset_code(
        username,
        normalized_email,
        code,
        ttl_minutes,
        cooldown_seconds,
    )
    if not created:
        return

    send_password_reset_template(
        recipient_email=normalized_email,
        recipient_name=username.strip() or "Investor",
        reset_code=code,
        expiry_minutes=ttl_minutes,
    )