from flask import Flask
import click
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'

    with app.app_context():
        from . import models  # noqa: F401 - ensure models are registered
        from .auth import auth_bp
        from .routes import main_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)

        # Flask CLI: create a user quickly from the terminal
        from .models import User, Role, db as _db  # type: ignore
        from .emailer import notify_email  # type: ignore

        @app.cli.command("create-user")
        @click.option("--name", prompt=True)
        @click.option("--email", prompt=True)
        @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
        @click.option("--role", type=click.Choice(Role.CHOICES), default=Role.MANAGER)
        def create_user(name, email, password, role):
            """Create a user (e.g., manager) for first login."""
            if _db.session.execute(_db.select(User).filter_by(email=email.lower())).scalar_one_or_none():
                click.echo("User already exists.")
                return
            u = User(name=name.strip(), email=email.lower(), role=role)
            u.set_password(password)
            _db.session.add(u)
            _db.session.commit()
            click.echo(f"Created {role} user: {email}")

        @app.context_processor
        def inject_unread_notifications():
            from .models import Notification  # local import to avoid circulars
            count = 0
            if hasattr(click, 'get_current_context') and getattr(click, 'get_current_context'):
                # avoid evaluating during CLI contexts
                pass
            try:
                from flask_login import current_user as cu
                if cu.is_authenticated:
                    count = _db.session.query(Notification).filter_by(user_id=cu.id, is_read=False).count()
            except Exception:
                count = 0
            return dict(unread_notifications=count)

        @app.cli.command("send-test-email")
        @click.option("--to", help="Override recipient (defaults to FORMSUBMIT_RECIPIENT)")
        @click.option("--subject", default="ASTO Test Notification")
        @click.option("--message", default="This is a test email from ASTO via Formsubmit.")
        def send_test_email(to, subject, message):
            """Send a test email to verify Formsubmit configuration."""
            cfg = app.config
            if not cfg.get('FORMSUBMIT_ENABLED'):
                click.echo("Formsubmit is disabled. Set FORMSUBMIT_ENABLED=1 in .env")
                return
            recipients = []
            if to:
                recipients = [to]
            elif cfg.get('FORMSUBMIT_PER_USER'):
                click.echo("Provide --to when FORMSUBMIT_PER_USER=1")
                return
            else:
                if not cfg.get('FORMSUBMIT_RECIPIENT'):
                    click.echo("Set FORMSUBMIT_RECIPIENT or pass --to")
                    return
                recipients = [cfg.get('FORMSUBMIT_RECIPIENT')]
            notify_email(recipients, subject, message)
            click.echo(f"Sent test email to: {', '.join(recipients)} (check inbox to verify Formsubmit)")

        @app.cli.command("seed-demo")
        def seed_demo():
            """Seed interactive demo content for dashboard, teams, open sessions, and notifications."""
            from datetime import datetime, timedelta
            from .models import Team, Event, Attendance, Notification

            def get_or_create_user(name, email, role, password):
                user = _db.session.execute(_db.select(User).filter_by(email=email)).scalar_one_or_none()
                if user:
                    return user, False
                user = User(name=name, email=email, role=role)
                user.set_password(password)
                _db.session.add(user)
                _db.session.flush()
                return user, True

            created = {
                "users": 0,
                "events": 0,
                "notifications": 0,
            }

            manager, was_created = get_or_create_user("Demo Manager", "manager@example.com", Role.MANAGER, "Manager123")
            created["users"] += int(was_created)
            leader, was_created = get_or_create_user("Demo Leader", "leader@example.com", Role.TEAM_LEADER, "Leader123")
            created["users"] += int(was_created)
            player, was_created = get_or_create_user("Demo Player", "player@example.com", Role.PLAYER, "Player123")
            created["users"] += int(was_created)

            team = _db.session.execute(_db.select(Team).filter_by(name="Demo United")).scalar_one_or_none()
            if not team:
                team = Team(name="Demo United", sport="Football", manager_id=manager.id)
                _db.session.add(team)
                _db.session.flush()

            manager.team_id = team.id
            leader.team_id = team.id
            player.team_id = team.id

            now = datetime.utcnow()
            event_specs = [
                {
                    "title": "Demo Training Session",
                    "event_type": "practice",
                    "offset_days": 1,
                    "location": "City Training Ground",
                    "is_open": False,
                    "capacity": 20,
                },
                {
                    "title": "Demo Open Session",
                    "event_type": "other",
                    "offset_days": 2,
                    "location": "Community Pitch",
                    "is_open": True,
                    "capacity": 12,
                },
                {
                    "title": "Demo Matchday",
                    "event_type": "match",
                    "offset_days": 3,
                    "location": "Northside Arena",
                    "is_open": False,
                    "capacity": 18,
                },
            ]

            seeded_events = {}
            for spec in event_specs:
                event = _db.session.execute(
                    _db.select(Event).filter_by(team_id=team.id, title=spec["title"])
                ).scalar_one_or_none()
                if not event:
                    event = Event(
                        title=spec["title"],
                        event_type=spec["event_type"],
                        start_time=now + timedelta(days=spec["offset_days"]),
                        location=spec["location"],
                        is_open=spec["is_open"],
                        capacity=spec["capacity"],
                        team_id=team.id,
                    )
                    _db.session.add(event)
                    _db.session.flush()
                    created["events"] += 1
                seeded_events[spec["title"]] = event

            for user, status in ((leader, "yes"), (player, "maybe")):
                existing = _db.session.execute(
                    _db.select(Attendance).filter_by(user_id=user.id, event_id=seeded_events["Demo Training Session"].id)
                ).scalar_one_or_none()
                if not existing:
                    _db.session.add(Attendance(user_id=user.id, event_id=seeded_events["Demo Training Session"].id, status=status))

            for user, status in ((leader, "yes"), (player, "yes")):
                existing = _db.session.execute(
                    _db.select(Attendance).filter_by(user_id=user.id, event_id=seeded_events["Demo Open Session"].id)
                ).scalar_one_or_none()
                if not existing:
                    _db.session.add(Attendance(user_id=user.id, event_id=seeded_events["Demo Open Session"].id, status=status))

            note_map = {
                manager.id: "Demo: Your team has 3 upcoming sessions. Check the dashboard for details.",
                leader.id: "Demo: Please review attendance for the next training session.",
                player.id: "Demo: You have a new open session available to join.",
            }
            for user_id, message in note_map.items():
                existing = _db.session.execute(
                    _db.select(Notification).filter_by(user_id=user_id, message=message)
                ).scalar_one_or_none()
                if not existing:
                    _db.session.add(Notification(user_id=user_id, message=message, is_read=False))
                    created["notifications"] += 1

            _db.session.commit()
            click.echo(
                "Demo seed complete "
                f"(users+{created['users']}, events+{created['events']}, notifications+{created['notifications']})."
            )

    return app
