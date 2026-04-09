from datetime import datetime, timedelta
from pathlib import Path

from app import db
from app.models import Attendance, Role, User

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
