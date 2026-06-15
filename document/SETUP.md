# School Management Portal Setup & Documentation

Welcome to the School Management Portal setup guide. This document contains the folder structure, database schema details, ER diagram, permission matrix, and setup instructions.

---

## 1. Directory & Folder Structure

```
d:\SchoolManagement/
├── app.py                  # Entrypoint: Creates app, registers blueprints, context filters
├── config.py               # Application configurations (SQLite connection parameters, key signatures)
├── database.py             # Instantiates db = SQLAlchemy() to prevent circular dependencies
├── decorators.py           # Custom authentication and authorization decorators
├── models.py               # SQLAlchemy Database Models (10 tables)
├── seed.py                 # Seeding script to populate permissions, roles, and default accounts
├── docs_security.md        # Risk assessment and security review
├── docs_architecture.md    # Architecture description and database migration plan
├── SETUP.md                # System configuration and user guide (This document)
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py             # Authentication routes (login, logout, self profile)
│   ├── academic.py         # Academic operations (Students, Teachers, Classes, Results)
│   ├── attendance.py       # Attendance tracking, marking, and percentage reports
│   └── announcements.py    # Announcement system & Approval workflows
│
├── static/
│   └── css/
│       └── portal.css      # Glassmorphic themes and interface animation styles
│
└── templates/
    ├── base.html           # Master layout with responsive navbar and flash notifications
    ├── dashboard.html      # Dynamic dashboard tailored to each of the 4 roles
    ├── auth/
    │   ├── login.html      # Styled login panel
    │   └── profile.html    # Profile page displaying account metrics
    ├── academic/
    │   ├── student_list.html
    │   ├── student_form.html
    │   ├── teacher_list.html
    │   ├── teacher_form.html
    │   ├── class_list.html
    │   ├── class_form.html
    │   ├── results.html
    │   ├── student_results.html
    │   └── result_form.html
    ├── attendance/
    │   ├── mark.html
    │   ├── report.html
    │   └── student_attendance.html
    ├── announcements/
    │   ├── list.html
    │   ├── create.html
    │   └── manage.html
    └── errors/
        ├── 403.html        # Custom Unauthorized Access page
        └── 404.html        # Custom Route Not Found page
```

---

## 2. Entity-Relationship (ER) Diagram

```
                +-------------------+
                |       roles       |
                +-------------------+
                | id (PK)           |
                | name (Unique)     |
                | description       |
                +-------------------+
                          | 1
                          |
                          | M
                +-------------------+
                |       users       |
                +-------------------+
                | id (PK)           |
                | username (Unique) |
                | password_hash     |
                | role_id (FK)      |-------------------------+
                | is_active         |                         |
                | created_at        |                         |
                +-------------------+                         |
                     /           \                            |
                   1/             \1                          |
                   /               \                          |
        +-------------------+    +-------------------+        |
        |     teachers      |    |     students      |        |
        +-------------------+    +-------------------+        |
        | id (PK)           |    | id (PK)           |        |
        | user_id (FK, UQ)  |    | user_id (FK, UQ)  |        |
        | name              |    | name              |        |
        | subject           |    | age               |        |
        | phone             |    | department        |        |
        +-------------------+    | class_id (FK)     |        |
                 | 1             | is_representative |        |
                 |               +-------------------+        |
                 | M                       |                  |
        +-------------------+              |                  |
        |      classes      |              |                  |
        +-------------------+              |                  |
        | id (PK)           |              |                  |
        | class_name        |              |                  |
        | section           |              |                  |
        | teacher_id (FK)   |              |                  |
        +-------------------+              |                  |
           | 1           | 1               |                  |
           |             +--------+        |                  |
           |                      |        |                  |
           | M                    | M      | M                | M
        +-------------------+  +-------------------+  +-------------------+
        |    attendance     |  |      results      |  |   announcements   |
        +-------------------+  +-------------------+  +-------------------+
        | id (PK)           |  | id (PK)           |  | id (PK)           |
        | student_id (FK)   |  | student_id (FK)   |  | title             |
        | class_id (FK)     |  | subject           |  | content           |
        | date              |  | marks             |  | class_id (FK)     |
        | status            |  | status            |  | created_by_id(FK) |
        | marked_by_id (FK) |  | marked_by_id (FK) |  | status            |
        +-------------------+  +-------------------+  | created_at        |
                                                      +-------------------+
```

---

## 3. Role-Based Access Control (RBAC) Permission Matrix

| Role | Students (CRUD) | Teachers (CRUD) | Classes (CRUD) | Attendance | Results | Announcements | Messages | System Settings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Principal** | Full CRUD | Full CRUD | Full CRUD | View all reports | View all | Create, Approve, View all | Send & receive all | Full access |
| **Teacher** | Read only | Read own / Edit self | Read only | Mark & view (assigned class) | Create & Update (assigned class) | Create (needs approval), View all | Send to class / principal | No access |
| **Student Representative** | Read own class | No access | Read own class | View own class reports | View own | Draft (needs approval), View own class | Send to class / teacher | No access |
| **Student** | Read own | No access | Read own | View own | View own | View approved | Send to teacher | No access |

---

## 4. Setup & Running Instructions

### Step 1: Install Required Dependencies
Ensure you have Python installed, then run:
```bash
pip install Flask Flask-SQLAlchemy SQLAlchemy
```

### Step 2: Seed the Database
Initialize the SQLite schema and seed the initial roles, permissions, classes, and test accounts:
```bash
python seed.py
```
*(On Windows systems, ensure you run this using your active Python environment executable).*

### Step 3: Run the Application
Start the Flask development server:
```bash
python app.py
```
Open a browser and navigate to `http://127.0.0.1:5000/`.

---

## 5. Seeded Test Accounts

Use these credentials to test the role-based behaviors:

1. **Principal User** (Complete Access)
   - Username: `principal`
   - Password: `password123`

2. **Teacher User** (Marking registers, grades, approving class drafts)
   - Username: `teacher1`
   - Password: `password123`

3. **Student Representative** (Class Leader - View class roster, class attendance, drafting announcements)
   - Username: `classleader1`
   - Password: `password123`

4. **Student User** (Standard student - View personal progress only)
   - Username: `student1`
   - Password: `password123`
