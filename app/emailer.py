import logging
import requests
from flask import current_app


def _endpoint_for(email: str) -> str:
    # Use AJAX endpoint to avoid redirects; server-side POST is fine
    return f"https://formsubmit.co/ajax/{email}"


def send_via_formsubmit(to_email: str, subject: str, message: str) -> bool:
    cfg = current_app.config
    if not cfg.get('FORMSUBMIT_ENABLED'):
        return False
    if not to_email:
        return False
    data = {
        'name': cfg.get('FORMSUBMIT_SENDER_NAME') or 'ASTO Notifications',
        'email': cfg.get('FORMSUBMIT_FROM') or 'no-reply@asto.local',
        'subject': f"{cfg.get('FORMSUBMIT_SUBJECT_PREFIX', '[ASTO]')} {subject}",
        'message': message,
        '_template': 'table',
    }
    try:
        resp = requests.post(_endpoint_for(to_email), data=data, timeout=8)
        if resp.status_code >= 200 and resp.status_code < 300:
            return True
        logging.warning("Formsubmit returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logging.exception("Formsubmit send failed: %s", e)
    return False


def notify_email(recipients: list[str], subject: str, message: str) -> None:
    cfg = current_app.config
    if not cfg.get('FORMSUBMIT_ENABLED'):
        return
    per_user = cfg.get('FORMSUBMIT_PER_USER')
    if per_user:
        for r in recipients:
            send_via_formsubmit(r, subject, message)
    else:
        agg = cfg.get('FORMSUBMIT_RECIPIENT')
        if agg:
            # include recipients list in body for aggregator context
            body = message + "\n\nRecipients:\n" + "\n".join(recipients)
            send_via_formsubmit(agg, subject, body)
