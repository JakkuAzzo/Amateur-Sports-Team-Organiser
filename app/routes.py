from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from .forms import TeamForm, EventForm, AddPlayerForm, RSVPForm
from .models import Team, User, Event, Role, Attendance, Notification
from .utils import roles_required, notify_team, notify_users
from . import db


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Simple role-adaptive dashboard
    if current_user.is_manager:
        teams = db.session.execute(db.select(Team)).scalars().all()
    elif current_user.is_team_leader and current_user.team_id:
        teams = [current_user.team]
    else:
        teams = [current_user.team] if current_user.team_id else []
    events = []
    if teams:
        team_ids = [t.id for t in teams if t]
        if team_ids:
            now = datetime.utcnow()
            events = db.session.execute(
                db.select(Event)
                .where(Event.team_id.in_(team_ids), Event.start_time >= now)
                .order_by(Event.start_time.asc())
                .limit(10)
            ).scalars().all()
    return render_template('dashboard.html', teams=teams, events=events)


@main_bp.route('/teams')
@login_required
def teams_index():
    if current_user.is_manager:
        teams = db.session.execute(db.select(Team)).scalars().all()
    else:
        teams = [current_user.team] if current_user.team else []
    return render_template('teams/index.html', teams=teams)


@main_bp.route('/teams/create', methods=['GET', 'POST'])
@login_required
@roles_required(Role.MANAGER)
def teams_create():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data.strip(), sport=form.sport.data.strip(), manager_id=current_user.id)
        db.session.add(team)
        db.session.commit()
        flash('Team created.', 'success')
        return redirect(url_for('main.teams_index'))
    return render_template('teams/create.html', form=form)


@main_bp.route('/teams/<int:team_id>')
@login_required
def team_detail(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        abort(404)
    # Access control: manager sees all; leader and members see their team
    if not current_user.is_manager:
        if not current_user.team_id or current_user.team_id != team.id:
            abort(403)
    add_player_form = AddPlayerForm()
    now = datetime.utcnow()
    upcoming_events = db.session.execute(
        db.select(Event)
        .where(Event.team_id == team.id, Event.start_time >= now)
        .order_by(Event.start_time.asc())
    ).scalars().all()
    return render_template('teams/detail.html', team=team, add_player_form=add_player_form, upcoming_events=upcoming_events)


@main_bp.route('/teams/<int:team_id>/add-player', methods=['POST'])
@login_required
def add_player(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        abort(404)
    # Only manager or team leader of this team
    if current_user.is_manager is False and not (current_user.is_team_leader and current_user.team_id == team.id):
        abort(403)
    form = AddPlayerForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data.lower())).scalar_one_or_none()
        if not user:
            flash('No user with that email. Ask them to register as Player, then add them.', 'warning')
        else:
            user.team_id = team.id
            if user.is_player is False:
                flash('User is not a Player; assigned to team anyway.', 'info')
            db.session.commit()
            flash('Player added to team.', 'success')
    return redirect(url_for('main.team_detail', team_id=team.id))


@main_bp.route('/teams/<int:team_id>/events/create', methods=['GET', 'POST'])
@login_required
def create_event(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        abort(404)
    # Only manager or team leader of this team
    if current_user.is_manager is False and not (current_user.is_team_leader and current_user.team_id == team.id):
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data.strip(),
            opponent=form.opponent.data.strip() if form.opponent.data else None,
            location=form.location.data.strip() if form.location.data else None,
            start_time=form.start_time.data,
            event_type=form.event_type.data,
            is_open=bool(form.is_open.data),
            capacity=form.capacity.data,
            team_id=team.id,
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created.', 'success')
        notify_team(team, f"New {event.event_type} scheduled: {event.title} on {event.start_time.strftime('%Y-%m-%d %H:%M')} at {event.location or 'TBD'}.",
                    email_subject=f"New {event.event_type}: {event.title}")
        return redirect(url_for('main.team_detail', team_id=team.id))
    return render_template('events/create.html', form=form, team=team)


@main_bp.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        abort(404)
    # Access: team members or manager; open sessions visible to all authenticated users
    if not event.is_open:
        if not current_user.is_manager and (not current_user.team_id or current_user.team_id != event.team_id):
            abort(403)
    attendance = db.session.execute(
        db.select(Attendance).filter_by(user_id=current_user.id, event_id=event.id)
    ).scalar_one_or_none()
    rsvp_form = RSVPForm(status=attendance.status if attendance else 'maybe')
    return render_template('events/detail.html', event=event, rsvp_form=rsvp_form, attendance=attendance)


@main_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def event_edit(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        abort(404)
    if current_user.is_manager is False and not (current_user.is_team_leader and current_user.team_id == event.team_id):
        abort(403)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.title = form.title.data.strip()
        event.opponent = form.opponent.data.strip() if form.opponent.data else None
        event.location = form.location.data.strip() if form.location.data else None
        event.start_time = form.start_time.data
        event.event_type = form.event_type.data
        event.is_open = bool(form.is_open.data)
        event.capacity = form.capacity.data
        db.session.commit()
        flash('Event updated.', 'success')
        # notify team members and attendees
        team_member_ids = [m.id for m in event.team.members]
        attendee_ids = [a.user_id for a in event.attendances]
        notify_users(set(team_member_ids + attendee_ids),
                     f"Event updated: {event.title} — {event.start_time.strftime('%Y-%m-%d %H:%M')} at {event.location or 'TBD'}.",
                     email_subject=f"Event updated: {event.title}")
        return redirect(url_for('main.event_detail', event_id=event.id))
    return render_template('events/edit.html', form=form, event=event)


@main_bp.route('/events/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        abort(404)
    # Team restriction if not open
    if not event.is_open:
        if not current_user.is_manager and (not current_user.team_id or current_user.team_id != event.team_id):
            abort(403)
    form = RSVPForm()
    if form.validate_on_submit():
        status = form.status.data
        att = db.session.execute(
            db.select(Attendance).filter_by(user_id=current_user.id, event_id=event.id)
        ).scalar_one_or_none()
        was_yes = att.status == 'yes' if att else False
        became_yes = False
        if not att:
            # If capacity set and full, disallow new YES
            if status == 'yes' and event.capacity is not None and event.remaining_slots == 0:
                flash('This session is full. Please select Maybe/No or try later.', 'warning')
                return redirect(url_for('main.event_detail', event_id=event.id))
            att = Attendance(user_id=current_user.id, event_id=event.id, status=status)
            db.session.add(att)
            became_yes = (status == 'yes')
        else:
            # Changing from non-yes to yes: check capacity
            if status == 'yes' and att.status != 'yes' and event.capacity is not None and event.remaining_slots == 0:
                flash('This session is full. Please select Maybe/No or try later.', 'warning')
                return redirect(url_for('main.event_detail', event_id=event.id))
            att.status = status
            became_yes = (status == 'yes' and not was_yes)
        db.session.commit()

        # Notify organiser if someone newly RSVP'd Yes
        if became_yes:
            organiser_ids = []
            if event.team.manager_id:
                organiser_ids.append(event.team.manager_id)
            # team leaders for this team
            leader_ids = [u.id for u in db.session.execute(
                db.select(User.id).filter(User.team_id == event.team_id, User.role == Role.TEAM_LEADER)
            ).all()]
            # db returns list of tuples (id,), normalize
            leader_ids = [lid[0] if isinstance(lid, tuple) else lid for lid in leader_ids]
            organiser_ids.extend(leader_ids)
            if organiser_ids:
                msg = f"{current_user.name} RSVP’d YES for {event.title} on {event.start_time.strftime('%Y-%m-%d %H:%M')} at {event.location or 'TBD'}."
                notify_users(set(organiser_ids), msg, email_subject=f"RSVP Yes: {event.title}")

        flash('Availability updated.', 'success')
        return redirect(url_for('main.event_detail', event_id=event.id))
    flash('Invalid submission.', 'danger')
    return redirect(url_for('main.event_detail', event_id=event.id))


@main_bp.route('/open-sessions')
@login_required
def open_sessions():
    now = datetime.utcnow()
    candidate_events = db.session.execute(
        db.select(Event).where(Event.is_open == True, Event.start_time >= now).order_by(Event.start_time.asc())  # noqa: E712
    ).scalars().all()
    events = [e for e in candidate_events if e.remaining_slots is None or e.remaining_slots > 0]
    return render_template('events/open.html', events=events)


@main_bp.route('/notifications')
@login_required
def notifications():
    notes = db.session.execute(
        db.select(Notification).filter_by(user_id=current_user.id).order_by(Notification.created_at.desc())
    ).scalars().all()
    return render_template('notifications/index.html', notifications=notes)


@main_bp.route('/notifications/<int:note_id>/read', methods=['POST'])
@login_required
def mark_note_read(note_id):
    note = db.session.get(Notification, note_id)
    if not note or note.user_id != current_user.id:
        abort(404)
    note.is_read = True
    db.session.commit()
    return redirect(url_for('main.notifications'))
