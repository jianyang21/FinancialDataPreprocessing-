# Finance Dashboard API

A role-based finance data processing and access control backend built with FastAPI and SQLite. Designed to serve a finance dashboard with user management, financial record CRUD, and summary analytics — all enforced by role-based access control.

---

## Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite via SQLAlchemy ORM
- **Authentication:** JWT tokens using PyJWT
- **Password Hashing:** bcrypt via passlib
- **Validation:** Pydantic v1

---

## Project Structure

```
finance_backend/
├── main.py              # Application entry point, router registration
├── database.py          # SQLAlchemy engine, session, and Base setup
├── models.py            # ORM models for User and FinancialRecord
├── schemas.py           # Pydantic request and response schemas
├── auth.py              # JWT token creation, decoding, and password hashing
├── dependencies.py      # FastAPI dependencies for auth and role enforcement
├── routers/
│   ├── auth.py          # Register, login, and current user endpoints
│   ├── users.py         # User management endpoints (admin only)
│   ├── records.py       # Financial record CRUD with filtering and pagination
│   └── dashboard.py     # Summary, category totals, recent activity, trends
└── requirements.txt
```

---

## Setup and Installation

**Step 1: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 2: Start the server**

```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Roles and Permissions

The system has three roles with increasing levels of access.

| Action                        | Viewer | Analyst | Admin |
|-------------------------------|--------|---------|-------|
| View financial records        | Yes    | Yes     | Yes   |
| View dashboard summary        | Yes    | Yes     | Yes   |
| View category totals          | Yes    | Yes     | Yes   |
| View recent activity          | Yes    | Yes     | Yes   |
| View monthly trends           | No     | Yes     | Yes   |
| Create financial records      | No     | Yes     | Yes   |
| Update financial records      | No     | Yes     | Yes   |
| Delete financial records      | No     | No      | Yes   |
| Manage users                  | No     | No      | Yes   |

The first user to register is automatically assigned the admin role. All subsequent registrations default to viewer.

---

## API Reference

### Authentication

| Method | Endpoint         | Description                        | Access  |
|--------|------------------|------------------------------------|---------|
| POST   | /auth/register   | Register a new user                | Public  |
| POST   | /auth/login      | Login and receive a JWT token      | Public  |
| GET    | /auth/me         | Get the current user's profile     | Any     |

### Users

All user management endpoints require the admin role.

| Method | Endpoint         | Description                        |
|--------|------------------|------------------------------------|
| GET    | /users/          | List all users                     |
| POST   | /users/          | Create a user with a specific role |
| GET    | /users/{id}      | Get a user by ID                   |
| PATCH  | /users/{id}      | Update a user's role or status     |
| DELETE | /users/{id}      | Delete a user                      |

### Financial Records

| Method | Endpoint          | Description                              | Access   |
|--------|-------------------|------------------------------------------|----------|
| GET    | /records/         | List records with filters and pagination | Viewer+  |
| POST   | /records/         | Create a new record                      | Analyst+ |
| GET    | /records/{id}     | Get a single record by ID                | Viewer+  |
| PATCH  | /records/{id}     | Update a record                          | Analyst+ |
| DELETE | /records/{id}     | Soft delete a record                     | Admin    |

**Available query parameters for GET /records/:**

- `type` — Filter by `income` or `expense`
- `category` — Partial text match on category
- `start_date` — Include records on or after this date
- `end_date` — Include records on or before this date
- `page` — Page number (default: 1)
- `limit` — Records per page (default: 20, max: 100)

### Dashboard

| Method | Endpoint               | Description                              | Access   |
|--------|------------------------|------------------------------------------|----------|
| GET    | /dashboard/summary     | Total income, expenses, and net balance  | Viewer+  |
| GET    | /dashboard/categories  | Totals grouped by category and type      | Viewer+  |
| GET    | /dashboard/recent      | Most recent N records                    | Viewer+  |
| GET    | /dashboard/trends      | Monthly income vs expense breakdown      | Analyst+ |

---

## Quick Start Example

**Register the first user (becomes admin automatically)**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "secret123"}'
```

**Login and get a token**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret123"}'
```

**Use the token for authenticated requests**

```bash
curl http://localhost:8000/dashboard/summary \
  -H "Authorization: Bearer <your_token_here>"
```

---

## Design Decisions and Assumptions

**Soft deletes:** Financial records are never permanently removed. Deleting a record sets an `is_deleted` flag, which excludes it from all queries. This preserves audit history.

**First user as admin:** Rather than a separate seed script, the first registered user automatically receives the admin role. This simplifies initial setup while keeping the logic self-contained.

**SQLite for storage:** SQLite was chosen for simplicity and zero-configuration setup. Switching to PostgreSQL or any other relational database requires only changing the `SQLALCHEMY_DATABASE_URL` value in `database.py`.

**JWT expiry:** Tokens expire after 24 hours. The `SECRET_KEY` in `auth.py` must be replaced with a secure random value before any deployment.

**Email validation:** Email fields are validated using a regex pattern. No external email validation library is required.

**Role enforcement:** Access control is implemented as FastAPI dependency functions in `dependencies.py`. Each router declares its required role directly in the endpoint signature, keeping authorization logic separate from business logic.

**Password minimum length:** Passwords must be at least 6 characters. No other complexity requirements are enforced, but these can be added in the `RegisterRequest` validator in `schemas.py`.
