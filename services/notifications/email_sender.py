import smtplib, logging
from email.message import EmailMessage
from datetime import datetime, timezone
from flask import current_app
from database import get_db
logger=logging.getLogger(__name__)
def send_email(subject, text_body, html_body):
    cfg=current_app.config
    ok=False; message="Email is not configured."
    try:
        required=[cfg["SMTP_HOST"],cfg["DIGEST_FROM_EMAIL"],cfg["DIGEST_TO_EMAIL"]]
        if not all(required): raise ValueError("SMTP host, sender, and recipient must be configured.")
        msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=cfg["DIGEST_FROM_EMAIL"]; msg["To"]=cfg["DIGEST_TO_EMAIL"]
        msg.set_content(text_body); msg.add_alternative(html_body,subtype="html")
        with smtplib.SMTP(cfg["SMTP_HOST"],cfg["SMTP_PORT"],timeout=15) as smtp:
            smtp.starttls()
            if cfg["SMTP_USERNAME"] and cfg["SMTP_PASSWORD"]: smtp.login(cfg["SMTP_USERNAME"],cfg["SMTP_PASSWORD"])
            smtp.send_message(msg)
        ok=True; message="Email provider confirmed message submission."
    except Exception as exc:
        message=str(exc)[:200]; logger.warning("Email delivery failed (%s)",type(exc).__name__)
    db=get_db()
    db.execute("INSERT INTO notification_attempts(channel,recipient_label,attempted_at,status,error_summary) VALUES(?,?,?,?,?)",
        ("email",cfg.get("DIGEST_TO_EMAIL",""),datetime.now(timezone.utc).isoformat(),"success" if ok else "failed","" if ok else message))
    db.commit()
    return {"ok":ok,"message":message}
