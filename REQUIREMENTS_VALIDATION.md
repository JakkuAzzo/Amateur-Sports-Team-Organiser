# Requirements Validation (All Met)

Date: 2026-04-05

This document records implementation and verification evidence for FR1-FR6 and NFR1-NFR4.

## Functional Requirements

### FR1 - Organiser authorisation control
Status: Met

Evidence:
- Public registration only creates `player` users in `app/auth.py`.
- Registration UI explicitly states elevated roles are organiser-assigned in `app/templates/auth/register.html`.
- Automated test: `test_fr1_public_registration_forces_player_role` in `tests/test_requirements_regressions.py`.
- Playwright run confirmed:
  - Registration shows player-role message.
  - Newly registered user receives `403` on `/teams/create` (cannot self-elevate).

### FR2 - Central view consistently shows upcoming sessions
Status: Met

Evidence:
- Dashboard filters sessions with `Event.start_time >= now` in `app/routes.py` (`dashboard`).
- Team detail view also filters upcoming events only in `app/routes.py` (`team_detail`).
- Automated test: `test_fr2_dashboard_shows_only_upcoming_events` in `tests/test_requirements_regressions.py`.
- Playwright run confirmed a newly created past session does not appear on dashboard.

### FR3 - Players can record availability for each session
Status: Met

Evidence:
- RSVP endpoint and UI available in `app/routes.py` (`rsvp`) and `app/templates/events/detail.html`.
- Supports yes/maybe/no values per event and per user.

### FR4 - Users notified when session details change
Status: Met

Evidence:
- In-app notifications are generated on event updates via `notify_users(...)` in `app/routes.py` (`event_edit`).
- Optional email notifications are integrated through Formsubmit (`app/emailer.py`, `README.md`).

### FR5 - Open-session controls available in normal create-event UI
Status: Met

Evidence:
- Event create form includes `is_open` and `capacity` fields in `app/forms.py` (`EventForm`).
- Controls are rendered in the standard create-event page `app/templates/events/create.html`.
- Automated test: `test_fr5_create_event_form_exposes_open_and_capacity_controls` in `tests/test_requirements_regressions.py`.

### FR6 - Open sessions shown only when extra participants are needed
Status: Met

Evidence:
- Open sessions query limits to future events and excludes full events in `app/routes.py` (`open_sessions`).
- Automated test: `test_fr6_open_sessions_only_future_and_needing_players` in `tests/test_requirements_regressions.py`.
- Playwright run confirmed:
  - Future open session with free capacity is shown.
  - Full open session is hidden.
  - Past open session is hidden.

## Non-Functional Requirements

### NFR1 - Suitability for users with limited technical experience
Status: Met

Evidence:
- Formal usability validation executed with Playwright task-based checks:
  - Task 1: Register and log in.
  - Task 2: Find team area and sessions from dashboard.
  - Task 3: Open a session and set RSVP.
- Outcome: Critical tasks complete without technical configuration steps in UI flow.
- Supporting design traits verified in UI: clear navigation labels, explicit role guidance, single-page dashboard summary.

### NFR2 - Mobile suitability
Status: Met

Evidence:
- Playwright mobile viewport verification performed at 390x844.
- Measured result: no horizontal overflow (`scrollWidth == innerWidth`), mobile nav toggle visible, core dashboard cards readable.
- Evidence screenshot: `playwright-mobile-dashboard.png`.

### NFR3 - Low-cost prototype stack
Status: Met

Evidence:
- Core stack remains free-to-run: Flask, SQLAlchemy, PostgreSQL, Bootstrap, pytest, Docker.
- Optional email path uses Formsubmit and can remain disabled for core operation.

### NFR4 - Reliable access to accurate information
Status: Met

Evidence:
- Upcoming/open-session filtering corrections ensure user-facing session data is time-accurate (`dashboard`, `team_detail`, `open_sessions`).
- Setup dependency reliability is protected by:
  - Explicit pins in `requirements.txt`.
  - Regression guard `test_nfr4_requirements_pin_core_runtime_dependencies` in `tests/test_requirements_regressions.py`.
- Verified test suite result: all requirement regression tests pass.

## Verification Summary

Commands and outcomes:
- `source .venv/bin/activate && pytest -q` -> `5 passed`.
- Playwright validation completed against running local app instance (desktop and mobile viewport).
