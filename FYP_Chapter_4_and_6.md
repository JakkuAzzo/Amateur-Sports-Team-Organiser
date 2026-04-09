# Chapter 4: Realisation

## 4.1 Chapter Overview

This chapter presents the realisation of the Amateur Sports Team Organiser (ASTO) as a working web application. The implementation translates the analysed stakeholder requirements (Chapter 2) into a usable system that supports session scheduling, availability tracking, organiser control, and open-session participation. In line with the CI6600 handbook guidance, this chapter explains how the artefact can be recreated, how it is used, and what output it generates, with supporting high-quality screenshots (Kingston University, 2025).

## 4.2 Intended Audience

The intended audience for this implementation section is:

- Final-year computing students who need to reproduce the prototype for marking or demonstration.
- Supervisors and assessors reviewing requirement traceability from design to implementation.
- Technical readers with basic familiarity with command-line tooling, Python virtual environments, and relational databases.

This section assumes that the reader can execute shell commands and read project configuration files but does not assume specialist knowledge of Flask internals.

## 4.3 Implementation Environment

### 4.3.1 Hardware Context

The prototype was implemented and validated on a standard developer laptop. No specialist hardware was required. This supports the project objective of a low-cost and accessible solution for volunteer-run teams.

### 4.3.2 Software Stack

ASTO was realised with the following software components:

- Flask for server-side web application structure and routing (Flask Software Foundation, 2026).
- Flask-Login for authenticated user sessions and role-aware access control (Flask-Login Contributors, 2026).
- Flask-WTF for form handling and CSRF protection (Flask-WTF Contributors, 2024).
- SQLAlchemy (via Flask-SQLAlchemy) for data modelling and persistence (SQLAlchemy Authors, 2026).
- Bootstrap-based responsive front-end patterns for mobile-friendly rendering (Bootstrap Team, 2026).
- pytest for automated requirement regression testing (pytest Development Team, 2026).
- Playwright for browser-based validation and screenshot evidence capture (Microsoft, 2026).

## 4.4 Steps to Recreate the Implementation

The implementation can be recreated with the following steps:

1. Clone or open the project folder.
2. Create and activate a virtual environment.
3. Install dependencies from requirements.txt.
4. Configure environment variables in .env.
5. Start the database service (or use SQLite for local validation).
6. Apply schema setup and seed demo data.
7. Run the Flask application.

An example command flow used during implementation and screenshot generation is shown below.

```bash
source .venv/bin/activate
export DATABASE_URL=sqlite:///chapter_media.db
export FLASK_APP=wsgi.py
python -c "from app import create_app, db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()"
flask seed-demo
flask run --host 127.0.0.1 --port 5000
```

These steps produce a ready-to-use local instance with demo users and events.

## 4.5 Steps to Use the Implementation and Generate Output

### 4.5.1 Authentication and Role Behaviour

The system provides login and role-based access control for manager, team leader, and player roles. Public registration creates player accounts only, while elevated roles are organiser-assigned. This prevents self-elevation in the normal sign-up flow and implements organiser-authorisation control required by FR1.

### 4.5.2 Team and Session Management

Managers and team leaders can:

- View team dashboards.
- Create events with title, time, location, and type.
- Mark sessions as open.
- Set capacity limits.

Players can:

- View upcoming sessions.
- RSVP as yes, maybe, or no.
- Receive updated session information through in-app notifications.

### 4.5.3 Open Session Workflow

When attendance is low, organisers can mark a session as open and set capacity. The open-sessions view presents future sessions that still have available places, supporting controlled participation and reducing cancellation risk.

## 4.6 Examples of Implementation Output (Screenshots)

### Figure 4.1 Dashboard Output (Desktop)

![Figure 4.1 Dashboard view showing teams and upcoming events](chapter4-dashboard-desktop-v3.png)

Figure 4.1 demonstrates that team and event information is consolidated in a single interface, supporting quick situational awareness for organisers and players.

### Figure 4.2 Create Event Output (Desktop)

![Figure 4.2 Event creation form showing open-session and capacity controls](chapter4-create-event-desktop-v3.png)

Figure 4.2 shows the normal create-event interface where open-session and capacity controls are directly available, addressing FR5 through the standard UI flow.

### Figure 4.3 Open Sessions Output (Desktop)

![Figure 4.3 Open sessions page for additional participants](chapter4-open-sessions-desktop-v3.png)

Figure 4.3 demonstrates the dedicated open-session listing used to advertise relevant sessions to additional players when participation is low.

### Figure 4.4 Notifications Output (Desktop)

![Figure 4.4 In-app notifications list for user updates](chapter6-notifications-desktop-v2.png)

Figure 4.4 shows the notification output channel used when session details are changed, supporting FR4.

## 4.7 Chapter 4 Conclusion

The ASTO implementation delivers a working artefact that maps directly to the identified coordination and participation problems in amateur sports teams. Core flows for session creation, RSVP, updates, and open-session participation are implemented in a way that remains lightweight and accessible. The artefact therefore satisfies the implementation intent of a practical, low-cost organiser while preserving scope control and usability focus (Sommerville, 2016; Pressman and Maxim, 2020).

---

# Chapter 6: Testing, Validation and Critical Review

## 6.1 Chapter Overview

This chapter evaluates ASTO against functional and non-functional requirements, documents testing and validation outcomes, and provides a critical review of project execution and results. The structure follows the handbook’s emphasis on realistic critical reflection, evidence-backed validation, and future development planning (Kingston University, 2025).

## 6.2 Testing and Validation Strategy

A mixed strategy was used:

- Automated backend regression tests using pytest for repeatable requirement checks.
- Browser-level validation using Playwright for end-to-end user flow confirmation.
- Mobile viewport validation for responsive behaviour evidence.
- Manual exploratory checks to confirm notification and session flows after automated runs.

This combination improves confidence by testing both logical correctness and real user interaction paths (Myers, Sandler and Badgett, 2011).

## 6.3 Functional Requirement Validation

### FR1 to FR6 Results

| ID | Requirement Summary | Validation Method | Result |
|---|---|---|---|
| FR1 | Organiser authorisation control | Registration + role access checks (pytest and Playwright) | Met |
| FR2 | Up-to-date upcoming session view | Dashboard filter tests and Playwright checks | Met |
| FR3 | Availability capture per session | RSVP flow inspection and route behaviour checks | Met |
| FR4 | Notification on session updates | Notification route/template verification and manual flow test | Met |
| FR5 | Open-session controls in normal create flow | UI test for open/capacity controls on create-event page | Met |
| FR6 | Open sessions filtered to those needing players | Query/filter verification + Playwright behaviour checks | Met |

Automated regression execution returned five passing tests:

```text
pytest -q
.....                                                                    [100%]
5 passed
```

The tested suite includes role registration constraints, upcoming-session filtering, open-session UI controls, open-session availability filtering, and dependency reliability checks.

## 6.4 Non-Functional Requirement Validation

| ID | Non-Functional Requirement | Evidence | Result |
|---|---|---|---|
| NFR1 | Usable by users with limited technical experience | Task-based Playwright walkthroughs of registration, login, dashboard, and RSVP | Met |
| NFR2 | Accessible on common mobile devices | Mobile viewport test at 390x844 with no horizontal overflow | Met |
| NFR3 | Free to use for organisers and players | Open-source stack and no paid core dependencies | Met |
| NFR4 | Reliable access to accurate session information | Time-based filtering + dependency guards + repeatable regression tests | Met |

### Figure 6.1 Mobile Validation Evidence

![Figure 6.1 Mobile dashboard rendering at 390x844](chapter6-dashboard-mobile-v2.png)

Mobile metrics recorded during validation:

- innerWidth = 390
- scrollWidth = 390
- horizontalOverflow = false

This evidence demonstrates responsive compatibility for the tested viewport configuration.

## 6.5 Critical Review of Project Outcomes

### 6.5.1 Review Against Aims and Objectives

The project aimed to provide a simple organiser for amateur teams and reduce confusion caused by fragmented communication channels. The delivered prototype meets this aim through centralised event visibility, explicit RSVP states, and organiser-led open-session controls. Validation indicates that previously partial requirements are now demonstrably met through both automated and browser-level evidence.

### 6.5.2 What Worked Well

- Requirement traceability from stakeholder analysis to feature delivery remained clear.
- Scope control prevented feature creep and protected usability.
- Regression tests provided reliable checks for critical behaviour.
- Playwright validation produced reproducible evidence suitable for report assessment.

### 6.5.3 What Could Be Improved

- Alembic migration behaviour with SQLite constraints required a workaround during local validation; future work should strengthen migration strategy consistency across development databases.
- Usability evidence would be stronger with a larger participant sample and SUS scoring rather than task completion only (Brooke, 1996).
- Notification evaluation should include measured delivery latency and user-response impact over longer periods.

## 6.6 Milestones, Deliverables and Time Management Review

Project delivery achieved the principal artefact and required report chapters, and produced supporting evidence assets. Iterative delivery, with frequent regression checks, reduced late-stage defects and allowed targeted correction of requirement gaps. However, testing instrumentation for broader user studies should have been planned earlier to increase empirical depth in evaluation.

## 6.7 Future Development

Future iterations should consider:

1. Integrated calendar sync (for example, iCal export) while preserving simplicity.
2. Better organiser analytics (attendance trends and dropout risk) with clear privacy controls.
3. Expanded user studies including accessibility and inclusivity testing.
4. Production-grade deployment hardening, including stricter observability and backup strategies.

## 6.8 Chapter 6 Conclusion

Testing and validation demonstrate that ASTO now meets FR1-FR6 and NFR1-NFR4 with evidence from automated tests, browser-based scenario validation, and mobile responsiveness checks. The critical review confirms that the project achieved its core purpose while identifying practical areas for technical and research enhancement.

---

# References (Harvard Style)

Bootstrap Team (2026) Bootstrap Documentation. Available at: https://getbootstrap.com/docs/ (Accessed: 5 April 2026).

Brooke, J. (1996) SUS: A quick and dirty usability scale. In: Jordan, P.W., Thomas, B., Weerdmeester, B.A. and McClelland, I.L. (eds.) Usability Evaluation in Industry. London: Taylor & Francis, pp. 189-194.

Flask Software Foundation (2026) Flask Documentation. Available at: https://flask.palletsprojects.com/ (Accessed: 5 April 2026).

Flask-Login Contributors (2026) Flask-Login Documentation. Available at: https://flask-login.readthedocs.io/ (Accessed: 5 April 2026).

Flask-WTF Contributors (2024) Flask-WTF Documentation. Available at: https://flask-wtf.readthedocs.io/ (Accessed: 5 April 2026).

Kingston University (2025) CI6600 Individual Project (Cyber Security): Project Information Handbook 2025-2026. Kingston upon Thames: Kingston University.

Microsoft (2026) Playwright Documentation. Available at: https://playwright.dev/docs/intro (Accessed: 5 April 2026).

Myers, G.J., Sandler, C. and Badgett, T. (2011) The Art of Software Testing. 3rd edn. Hoboken, NJ: John Wiley & Sons.

Pressman, R.S. and Maxim, B.R. (2020) Software Engineering: A Practitioner’s Approach. 9th edn. New York: McGraw-Hill.

pytest Development Team (2026) pytest Documentation. Available at: https://docs.pytest.org/ (Accessed: 5 April 2026).

SQLAlchemy Authors (2026) SQLAlchemy Documentation. Available at: https://docs.sqlalchemy.org/ (Accessed: 5 April 2026).

Sommerville, I. (2016) Software Engineering. 10th edn. Harlow: Pearson.
