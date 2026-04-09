from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from . import db, login_manager


class Role:
    MANAGER = "manager"
    TEAM_LEADER = "team_leader"
    PLAYER = "player"

    CHOICES = [MANAGER, TEAM_LEADER, PLAYER]


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    sport = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager = relationship("User", foreign_keys=[manager_id])

    members = relationship("User", back_populates="team", foreign_keys="User.team_id")
    events = relationship("Event", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Team {self.name}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=Role.PLAYER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_manager(self) -> bool:
        return self.role == Role.MANAGER

    @property
    def is_team_leader(self) -> bool:
        return self.role == Role.TEAM_LEADER

    @property
    def is_player(self) -> bool:
        return self.role == Role.PLAYER

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    opponent = db.Column(db.String(140))
    location = db.Column(db.String(140))
    start_time = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default="practice")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_open = db.Column(db.Boolean, nullable=False, default=False)
    capacity = db.Column(db.Integer)  # optional max attendees

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team = relationship("Team", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event {self.title} ({self.event_type})>"

    @property
    def attending_yes(self):
        return [a for a in self.attendances if a.status == 'yes']

    @property
    def remaining_slots(self):
        if self.capacity is None:
            return None
        return max(self.capacity - len(self.attending_yes), 0)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='maybe')  # yes/no/maybe
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User')
    event = relationship('Event', backref=db.backref('attendances', cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_attendance_user_event'),)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = relationship('User')
