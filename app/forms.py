from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateTimeLocalField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from .models import Role


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Create Account")


class TeamForm(FlaskForm):
    name = StringField("Team Name", validators=[DataRequired(), Length(min=2, max=120)])
    sport = StringField("Sport", validators=[DataRequired(), Length(min=2, max=80)])
    submit = SubmitField("Save Team")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=140)])
    opponent = StringField("Opponent", validators=[Length(max=140)])
    location = StringField("Location", validators=[Length(max=140)])
    start_time = DateTimeLocalField("Start Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()], default=datetime.utcnow)
    event_type = SelectField("Type", choices=[("practice", "Practice"), ("match", "Match"), ("other", "Other")], validators=[DataRequired()])
    is_open = BooleanField("Open Session (allow guests)")
    capacity = IntegerField("Capacity", validators=[Optional(), NumberRange(min=1, max=1000)])
    submit = SubmitField("Create Event")


class AddPlayerForm(FlaskForm):
    email = StringField("Player Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Add Player")


class RSVPForm(FlaskForm):
    status = SelectField("Your Availability", choices=[("yes", "Yes"), ("maybe", "Maybe"), ("no", "No")], validators=[DataRequired()])
    submit = SubmitField("Update")


class TeamMessageForm(FlaskForm):
    message = TextAreaField("Team Message", validators=[DataRequired(), Length(min=2, max=500)])
    submit = SubmitField("Post Message")
