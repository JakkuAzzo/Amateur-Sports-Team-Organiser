from datetime import datetime, timedelta
from pathlib import Path

from app import db
from app.models import Attendance, Role, User, TeamMessage, Notification

from .conftest import create_event, create_team_with_manager, create_user, login


def test_nfr4_requirements_pin_core_runtime_dependencies():
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    content = requirements.read_text(encoding="utf-8")

    # Guard against accidental removal of core app dependencies.
    assert "Flask-SQLAlchemy==" in content
    assert "Flask-Migrate==" in content


def test_fr1_public_registration_forces_player_role(client, app_ctx):
    response = client.post(
        "/auth/register",
        data={
            "name": "Public User",
            "email": "public@example.com",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    created = db.session.execute(db.select(User).filter_by(email="public@example.com")).scalar_one()
    assert created.role == Role.PLAYER


def test_fr2_dashboard_shows_only_upcoming_events(client, app_ctx):
    team, manager = create_team_with_manager()
    create_event(team.id, "Past Session", datetime.utcnow() - timedelta(days=1), is_open=False)
    create_event(team.id, "Upcoming Session", datetime.utcnow() + timedelta(days=1), is_open=False)

    login(client, manager.email)
    response = client.get("/dashboard")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Upcoming Session" in body
    assert "Past Session" not in body


def test_fr5_create_event_form_exposes_open_and_capacity_controls(client, app_ctx):
    team, manager = create_team_with_manager("Lions", "Basketball")
    login(client, manager.email)

    response = client.get(f"/teams/{team.id}/events/create")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Open Session" in body
    assert "Capacity" in body


def test_fr6_open_sessions_only_future_and_needing_players(client, app_ctx):
    team, manager = create_team_with_manager("Tigers", "Cricket")
    outsider = create_user("Guest", "guest@example.com", Role.PLAYER)

    future_open_available = create_event(
        team.id,
        "Future Open Available",
        datetime.utcnow() + timedelta(days=2),
        is_open=True,
        capacity=2,
    )
    future_open_full = create_event(
        team.id,
        "Future Open Full",
        datetime.utcnow() + timedelta(days=3),
        is_open=True,
        capacity=1,
    )
    create_event(
        team.id,
        "Past Open",
        datetime.utcnow() - timedelta(hours=2),
        is_open=True,
        capacity=5,
    )

    db.session.add(Attendance(user_id=outsider.id, event_id=future_open_full.id, status="yes"))
    db.session.commit()

    login(client, outsider.email)
    response = client.get("/open-sessions")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert future_open_available.title in body
    assert future_open_full.title not in body
    assert "Past Open" not in body


def test_team_message_feed_allows_posting_and_persists(client, app_ctx):
    team, manager = create_team_with_manager("Wolves", "Football")
    member = create_user("Member", "member@example.com", Role.PLAYER, team=team)
    db.session.commit()

    login(client, manager.email)
    response = client.post(
        f"/teams/{team.id}/messages",
        data={"message": "Training moved to 19:00"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    stored = db.session.execute(db.select(TeamMessage).filter_by(team_id=team.id)).scalars().all()
    assert any(m.message == "Training moved to 19:00" for m in stored)
    # teammates should receive an in-app notification
    teammate_notes = db.session.execute(db.select(Notification).filter_by(user_id=member.id)).scalars().all()
    assert any("Training moved to 19:00" in n.message for n in teammate_notes)


def test_event_reminder_creates_notifications_for_unconfirmed_members(client, app_ctx):
    team, manager = create_team_with_manager("Falcons", "Football")
    maybe_user = create_user("Maybe User", "maybe@example.com", Role.PLAYER, team=team)
    yes_user = create_user("Yes User", "yes@example.com", Role.PLAYER, team=team)
    event = create_event(team.id, "Reminder Session", datetime.utcnow() + timedelta(days=1), is_open=False, capacity=10)

    db.session.add(Attendance(user_id=yes_user.id, event_id=event.id, status="yes"))
    db.session.add(Attendance(user_id=maybe_user.id, event_id=event.id, status="maybe"))
    db.session.commit()

    login(client, manager.email)
    response = client.post(f"/events/{event.id}/remind", follow_redirects=True)

    assert response.status_code == 200
    maybe_notes = db.session.execute(db.select(Notification).filter_by(user_id=maybe_user.id)).scalars().all()
    yes_notes = db.session.execute(db.select(Notification).filter_by(user_id=yes_user.id)).scalars().all()
    assert any("Reminder Session" in n.message for n in maybe_notes)
    assert not any("Reminder Session" in n.message for n in yes_notes)
