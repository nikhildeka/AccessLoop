# AccessLoop

### Unlock Underused Equipment and Spaces

AccessLoop is a campus resource-sharing platform designed to make underutilised equipment and spaces easier to discover, request, book, and manage.

Instead of allowing useful campus resources to remain unused, AccessLoop provides a centralised platform where students can discover available resources and owners can manage booking requests and equipment usage.

## Problem Statement

Educational institutions often have equipment and spaces that remain underutilised because students cannot easily discover their availability or request access. Manual booking processes can also make approvals, tracking, and accountability difficult.

AccessLoop aims to address these challenges through a digital resource-sharing workflow.

## Key Features

* **Resource Discovery:** Browse and search available campus resources.
* **Booking Management:** Submit booking requests and track their status.
* **Role-Based Access:** Separate student, owner, manager, and administrator workflows.
* **Owner Approvals:** Approve or reject resource booking requests.
* **Equipment Lifecycle:** Track approval, check-in, check-out, and return.
* **Incident Reporting:** Report damaged equipment, missing accessories, and technical issues.
* **Incident Resolution:** Allow authorised users to review and resolve reported incidents.
* **Secure Authentication:** Login, logout, password handling, and CSRF protection.

## Technology Stack

* Python
* Flask
* Flask-SQLAlchemy
* SQLite
* Flask-Login
* Flask-WTF
* Flask-Limiter
* HTML and CSS
* Jinja2
* Git and GitHub

## Application Workflow

1. Students discover available resources.
2. Students submit booking requests.
3. Resource owners review requests.
4. Approved bookings proceed to equipment check-in.
5. Equipment is tracked through its usage and return.
6. Users can report incidents.
7. Authorised users review and resolve incidents.

## Project Structure

```text
AccessLoop/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── seed.py
├── requirements.txt
├── routes/
├── services/
├── templates/
├── tests/
└── CHECKLIST.md
```

## Run Locally

Clone the repository:

```bash
git clone https://github.com/nikhildeka/AccessLoop.git
cd AccessLoop
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a private `.env` file containing:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///accessloop.db
SESSION_COOKIE_SECURE=0
```

Initialise the database:

```bash
flask --app app init-db
```

Run the application:

```bash
python app.py
```

## Live Demo

https://nikhildeka.pythonanywhere.com

## Repository

https://github.com/nikhildeka/AccessLoop

## Future Scope

* QR-code-based equipment check-in and check-out.
* Email and in-app booking notifications.
* Analytics for resource utilisation.
* Calendar-based availability management.
* Integration with institutional identity systems.
* Support for multiple campuses.

## Project Information

**Project:** AccessLoop
**Problem Statement:** Unlock Underused Equipment and Spaces
**Development:** Individual project
**Status:** Working MVP deployed online

This project was developed as a hackathon MVP. AI tools were used as development assistance where applicable; implementation and testing were performed as part of the project workflow.
