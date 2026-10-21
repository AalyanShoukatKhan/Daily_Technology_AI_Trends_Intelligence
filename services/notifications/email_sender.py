
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import current_app
from database import get_db

logger = logging.getLogger(__name__)


def send_email(subject, text_body, html_body):
    cfg = current_app.config
    ok = False
    message = "Email is not configured."

    try:
        required = [
            cfg.get("SMTP_HOST"),
            cfg.get("DIGEST_FROM_EMAIL"),
            cfg.get("DIGEST_TO_EMAIL"),
        ]

        if not all(required):
            raise ValueError(
                "SMTP host, sender, and recipient must be configured."
            )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = cfg["DIGEST_FROM_EMAIL"]
        msg["To"] = cfg["DIGEST_TO_EMAIL"]

        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(
            cfg["SMTP_HOST"],
            int(cfg.get("SMTP_PORT", 587)),
            timeout=30,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()

            username = cfg.get("SMTP_USERNAME")
            password = cfg.get("SMTP_PASSWORD")

            if username and password:
                smtp.login(username, password)

            smtp.send_message(msg)

        ok = True
        message = "Email provider confirmed message submission."

    except Exception as exc:
        message = str(exc)[:200]
        logger.warning(
            "Email delivery failed (%s): %s",
            type(exc).__name__,
            message,
        )

    db = get_db()
    db.execute(
        """
        INSERT INTO notification_attempts
        (channel, recipient_label, attempted_at, status, error_summary)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "email",
            cfg.get("DIGEST_TO_EMAIL", ""),
            datetime.now(timezone.utc).isoformat(),
            "success" if ok else "failed",
            "" if ok else message,
        ),
    )
    db.commit()

    return {"ok": ok, "message": message}
