import os
from datetime import datetime
from uuid import uuid4

import pytest

from app import create_app, db
from app.models import Event, Role, Team, User


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret"

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        yield


def create_user(name: str, email: str, role: str, password: str = "password123", team=None):
    user = User()
    user.name = name
    user.email = email
    user.role = role
    user.team = team
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email: str, password: str = "password123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def create_team_with_manager(team_name: str = "Eagles", sport: str = "Football"):
    manager_email = f"manager-{uuid4().hex[:8]}@example.com"
    manager = create_user("Manager", manager_email, Role.MANAGER)
    team = Team(name=team_name, sport=sport, manager_id=manager.id)
    db.session.add(team)
    db.session.commit()
    manager.team_id = team.id
    db.session.commit()
    return team, manager


def create_event(team_id: int, title: str, start_time: datetime, is_open: bool, capacity=None):
    event = Event(
        title=title,
        event_type="practice",
        start_time=start_time,
        team_id=team_id,
        is_open=is_open,
        capacity=capacity,
    )
    db.session.add(event)
    db.session.commit()
    return event
