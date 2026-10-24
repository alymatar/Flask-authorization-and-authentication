# Flask Authentication & Authorization API

![tests](https://github.com/alymatar/Flask-authorization-and-authentication/actions/workflows/tests.yml/badge.svg)

A REST API built with Flask, SQLAlchemy and PostgreSQL that implements authentication and role-based access control (RBAC) from scratch: no Flask-Login and no Flask-JWT extensions.

I built it to understand how JWT, server-side sessions and permission systems work underneath the libraries that usually hide them.

## Features

**Authentication**
- Register and log in with email and password
- Passwords hashed with bcrypt (12 rounds)
- Password rules enforced at registration: 6–50 characters with an uppercase letter, a lowercase letter, a digit and a special character, plus a matching confirmation field
- Two ways to authenticate on every request:
  - JWT access token in the `Authorization: Bearer` header (HS256, 1 hour by default)
  - Session cookie (`session_id`, HttpOnly, SameSite=Lax) backed by a `sessions` table, valid for 7 days
- Refresh tokens (30 days by default) to get a new access token
- Logout deletes the server-side session and clears the cookie
- Users can list their active sessions and end any session except the current one
- Soft delete: deleting an account sets `is_active = False`, and inactive users can't authenticate

**Authorization (RBAC)**
- Roles (`admin`, `manager`, `user`, `guest`) have rules per business element (`products`, `orders`, `users`, ...)
- Each rule has separate flags: read own / read all, create, update own / update all, delete own / delete all
- Ownership checks: a user with "own" permission can change only resources they created
- List endpoints return everything for roles with "read all", and only the caller's own records otherwise
- Admin API to manage roles, business elements, permission rules and user roles at runtime
- System roles can't be edited or deleted, and a role assigned to users can't be deleted

**Engineering**
- App factory pattern with blueprints
- Request validation with marshmallow schemas
- Reusable decorators: `@login_required`, `@permission_required(element, action)`, `@admin_required`, `@optional_login`
- JSON error handlers for 400, 401, 403, 404 and 500
- CORS configured for a local frontend
- 16 pytest tests that run on in-memory SQLite, so no database server is needed

## Tech stack

| | |
|---|---|
| Language | Python 3 |
| Framework | Flask 2.3 |
| Database | PostgreSQL, via Flask-SQLAlchemy (SQLAlchemy 2.0) and psycopg2 |
| Migrations | Flask-Migrate (installed and initialised) |
| Auth | PyJWT, bcrypt |
| Validation | marshmallow |
| Testing | pytest, pytest-flask |

## Architecture

```text
app/
├── __init__.py          # app factory, extensions, blueprints, error handlers
├── models/              # User, Role, Session, BusinessElement, AccessRoleRule
├── routes/              # auth, users, products, orders, admin blueprints
├── schemas/             # marshmallow validation for users and permission rules
├── services/
│   ├── auth_service.py        # JWT creation/validation, DB sessions, refresh
│   └── permission_service.py  # permission helpers
├── utils/decorators.py  # login_required, permission_required, admin_required
└── tests/               # pytest suites for auth and permissions
config.py                # Config (reads .env) and TestConfig (in-memory SQLite)
init_db.py               # creates tables and seeds roles, rules and demo users
run.py                   # development entry point
```

How a protected request is checked:

```text
request
  → @login_required        find the user from the Bearer token, or else the session cookie
  → @permission_required   load the rule for (user's role, business element)
  → User.has_permission    check the flag, plus ownership for "own" permissions
  → view                   allowed, or 401 / 403
```

### Data model

| Table | Key columns |
|---|---|
| `users` | `id`, `email` (unique), `password_hash`, `first_name`, `last_name`, `patronymic`, `is_active`, `role_id` → roles, `last_login_at`, `last_login_ip` |
| `roles` | `id`, `name` (unique), `description`, `is_system_role` |
| `sessions` | `id` (UUID token), `user_id` → users, `expires_at`, `ip_address`, `user_agent` |
| `business_elements` | `id`, `name` (unique), `description` |
| `access_role_rules` | `role_id`, `element_id` (unique together), `read`, `read_all`, `create`, `update`, `update_all`, `delete`, `delete_all` flags |

> Products and orders are **demo resources**: they are kept in memory inside the route modules so the permission system has something to protect. Users, roles, sessions and rules are stored in PostgreSQL.

## API endpoints

**Auth**: `/api/auth`

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/register` | public | Create an account (gets the `user` role) |
| POST | `/login` | public | Returns `access_token` and `refresh_token`, and sets the `session_id` cookie |
| POST | `/refresh` | public | Exchange a `refresh_token` for a new access token |
| POST | `/logout` | cookie | Delete the current session and clear the cookie |
| GET | `/me` | logged in | Current user's profile |
| GET | `/check` | public | Whether the request is authenticated |

**Users**: `/api/users`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/<id>` | `users:read` | A user's profile (own profile, or any with "read all") |
| PUT | `/<id>` | self | Update own profile |
| DELETE | `/<id>` | self | Soft-delete own account |
| GET | `/<id>/sessions` | self | List own active sessions |
| DELETE | `/<id>/sessions/<session_id>` | self | End another session (not the current one) |

**Demo resources**: `/api/products` and `/api/orders`

| Method | Path | Permission |
|---|---|---|
| GET | `/api/products`, `/api/products/<id>` | `products:read` |
| POST | `/api/products` | `products:create` |
| PUT | `/api/products/<id>` | `products:update` (+ ownership) |
| DELETE | `/api/products/<id>` | `products:delete` (+ ownership) |
| GET | `/api/orders`, `/api/orders/<id>` | `orders:read` |
| POST | `/api/orders` | `orders:create` |
| POST | `/api/orders/<id>/cancel` | `orders:update` (+ ownership) |

**Admin** (`admin` role only): `/api/admin`

| Method | Path | Description |
|---|---|---|
| GET, POST | `/roles` | List or create roles |
| PUT, DELETE | `/roles/<id>` | Edit or delete a non-system role |
| GET, POST | `/elements` | List or create business elements |
| GET, POST | `/permissions` | List or create permission rules |
| PUT, DELETE | `/permissions/<id>` | Edit or delete a rule |
| GET | `/users` | List users |
| PUT | `/users/<id>/role` | Change a user's role |
| GET | `/stats` | Counts of users, roles and rules |

### Default roles (seeded by `init_db.py`)

| Role | Products | Orders | Users |
|---|---|---|---|
| admin | everything | everything | everything (plus all other elements) |
| manager | read all, create, update all, delete own | read all, create, update own | read all |
| user | read all, create, update/delete own | read, create, update own | — |
| guest | read all | — | — |

## Run locally

**Requirements:** Python 3.10+ and PostgreSQL. If you have Docker, this starts a local Postgres:

```bash
docker run --name flask-auth-db -e POSTGRES_PASSWORD=<choose-a-password> \
  -e POSTGRES_DB=flask_auth -p 5432:5432 -d postgres:16
```

```bash
git clone https://github.com/alymatar/Flask-authorization-and-authentication.git
cd Flask-authorization-and-authentication

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then edit .env with your own values
python init_db.py                 # creates tables, roles, rules and demo users
python run.py                     # http://127.0.0.1:5000
```

`.env` holds `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL` and the optional token lifetimes. It is git-ignored; `.env.example` lists every variable with placeholder values.

`init_db.py` creates four demo accounts (`admin@`, `manager@`, `user@` and `guest@example.com`) and prints their passwords. They're for local testing only.

### Try it with curl

```bash
# 1. Register
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"Secret123!","password_confirm":"Secret123!","first_name":"Jane","last_name":"Doe"}'

# 2. Log in and copy the access_token from the response
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"Secret123!"}'

# 3. Call a protected route
curl http://127.0.0.1:5000/api/auth/me -H "Authorization: Bearer <access_token>"

# 4. A regular user calling an admin route gets 403 Forbidden
curl http://127.0.0.1:5000/api/admin/roles -H "Authorization: Bearer <access_token>"
```

## Tests

```bash
pytest
```

The tests use `TestConfig` (in `config.py`), which points SQLAlchemy at in-memory SQLite, so they run without PostgreSQL or a `.env` file. GitHub Actions runs them on every push (`.github/workflows/tests.yml`).

They cover:
- **Auth:** registration, duplicate email, password mismatch, weak password, login success and failure, logout, token refresh, current user
- **Permissions:** admin vs. user on admin routes, reading and creating products, updating someone else's product as admin (allowed) and as a regular user (denied), creating orders

## Security notes and next steps

Already in place: bcrypt hashing, short-lived access tokens, HttpOnly session cookies, inactive accounts blocked, secrets read from environment variables.

Before production I would add:
- Rate limiting on login and registration
- `Secure` cookies behind HTTPS
- Refresh-token rotation and revocation
- Persisting products and orders in the database instead of in memory
- Alembic migrations instead of `db.create_all()`
- A Dockerfile and docker-compose setup
