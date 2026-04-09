from functools import wraps
from flask import abort
from flask_login import current_user
from . import db
from .models import Notification, User
from .emailer import notify_email


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def notify_users(user_ids, message: str, email_subject: str | None = None):
    notes = [Notification(user_id=uid, message=message) for uid in user_ids]
    if notes:
        db.session.add_all(notes)
        db.session.commit()
    # Email (optional)
    if email_subject:
        recipients = [u.email for u in db.session.query(User.email).filter(User.id.in_(user_ids)).all()]
        # query(User.email) returns list of tuples; normalize to strings
        recipients = [r[0] if isinstance(r, tuple) else r for r in recipients]
        notify_email(recipients, email_subject, message)


def notify_team(team, message: str, email_subject: str | None = None):
    if not team:
        return
    user_ids = [m.id for m in team.members]
    notify_users(user_ids, message, email_subject=email_subject)
