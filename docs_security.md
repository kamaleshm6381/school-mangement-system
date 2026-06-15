# Security Review & Risk Assessment

This document outlines the security risks associated with school management systems and the specific architectural and programmatic mitigations implemented in this portal.

---

## Identified Security Risks, Impacts, and Mitigations

### 1. Plaintext Password Storage
* **Risk**: Storing passwords in plaintext (as done in the original project) means a database breach compromises all user credentials.
* **Impact**: Total compromise of all accounts (Principal, Teachers, Students), leading to identity theft and database tampering.
* **Mitigation**: Implemented Werkzeug's secure password hashing algorithm (`scrypt:262144:8:1`). Passwords are never stored in plaintext. They are hashed before storage using `generate_password_hash` and verified using `check_password_hash`.

### 2. Broken Object Level Authorization (BOLA / IDOR)
* **Risk**: Students changing the ID parameter in URLs (e.g., `/academic/results/student/2`) to view other students' grades.
* **Impact**: Unauthorized access to private student academic and attendance records, violating privacy laws (FERPA/GDPR).
* **Mitigation**: Added strict ownership checks in the route handlers in `blueprints/academic.py` and `blueprints/attendance.py`. Standard students are restricted: if they try to access records where the student ID does not match their logged-in profile ID, the system responds with a `403 Forbidden` error.

### 3. Deleted or Deactivated Users with Active Sessions
* **Risk**: If a user is deleted or deactivated by the Principal, their current browser session remains valid until the session cookie expires.
* **Impact**: Malicious former staff or students retaining access to mutate records after deactivation.
* **Mitigation**: Implemented a `@app.before_request` hook in `app.py` that queries the database for the user record matching the active `session['user_id']`. If the user is missing or has `is_active = False`, the session is cleared instantly and the request is redirected to the login page.

### 4. Privilege Escalation via POST Param Manipulation
* **Risk**: A user modifying hidden form inputs (e.g. `role_id` or `is_representative`) during student creation or update requests.
* **Impact**: Standard student promoting themselves to a Student Representative or Teacher, gaining access to view classmates' attendance summaries or draft announcements.
* **Mitigation**: Implemented strict server-side decorators (`@role_required('Principal')` and `@permission_required`) on all administrative POST handlers. Role assignments are validated against the database-backed role hierarchy, ignoring arbitrary client inputs.

### 5. SQL Injection (SQLi)
* **Risk**: User input in forms (like username search) passed directly to raw SQL query strings.
* **Impact**: Attackers executing arbitrary SQL commands, dumping the entire database, or bypassing authentication.
* **Mitigation**: Replaced all raw SQLite queries with SQLAlchemy ORM. SQLAlchemy uses parameterized queries (Prepared Statements) natively, separating SQL logic from user inputs and entirely neutralizing SQL Injection vectors.

### 6. Cross-Site Scripting (XSS)
* **Risk**: Malicious scripts uploaded via announcement text fields rendering in other users' dashboards.
* **Impact**: Stealing session cookies, hijacking pages, or performing unauthorized actions in the administrator's context.
* **Mitigation**: Utilized Jinja2 templates, which natively apply auto-escaping for HTML and JavaScript elements. Dynamic variables are rendered as raw text rather than active script elements unless explicitly marked safe (which is restricted).

### 7. Session Fixation and Hijacking
* **Risk**: Attacker intercepting a user's session cookie or pre-setting a session cookie value.
* **Impact**: Hijacking a logged-in principal's session, taking full control of the application.
* **Mitigation**: Secure session management:
  1. Configured Flask to sign session cookies with a cryptographically strong `SECRET_KEY`.
  2. Implemented `session.clear()` immediately upon a successful login post to invalidate any pre-login session states, preventing session fixation.
  3. Browser cookies are marked `HttpOnly` by default in Flask, preventing access from client-side scripts.

### 8. Compromised Administrator Account
* **Risk**: A principal account password being cracked or leaked.
* **Impact**: Complete school records disclosure, deletion, or manipulation.
* **Mitigation**: Administrative actions are separated into granular permissions. Seeding logic limits critical commands. We recommend enforcing high-entropy passwords (e.g., minimum 12 characters, symbols, numbers) and adding log audits for administrative actions.

### 9. Technical Information Disclosure
* **Risk**: Exposing raw error stack traces, database schema layouts, or local file system structures to end-users during a crash.
* **Impact**: Giving hackers targeted intelligence about server architecture and database engines to orchestrate exploits.
* **Mitigation**: Configured custom HTTP error blueprints in `app.py` for `403` and `404` pages. Disabled debug modes in testing/production settings to prevent execution console rendering.

### 10. Cross-Site Request Forgery (CSRF)
* **Risk**: Attackers hosting malicious pages that submit post requests (like deletion commands) to the portal in the background while the administrator is logged in.
* **Impact**: Unauthorized changes, additions, or deletions of student records.
* **Mitigation**: For production environments, it is highly recommended to integrate `Flask-WTF` which injects unique, one-time CSRF tokens into all HTML forms. All POST handlers then validate this token before execution.
