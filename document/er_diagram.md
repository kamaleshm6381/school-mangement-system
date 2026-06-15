# Entity-Relationship (ER) Diagram

Below is the database schema for the school portal. This includes all 11 tables (including the user roles, permissions, academic data, attendance logs, results, announcements, and messages) and their corresponding relationships.

```mermaid
erDiagram
    ROLES {
        int id PK
        string name
        string description
    }
    PERMISSIONS {
        int id PK
        string name
        string description
    }
    ROLE_PERMISSIONS {
        int role_id PK, FK
        int permission_id PK, FK
    }
    USERS {
        int id PK
        string username
        string password_hash
        int role_id FK
        boolean is_active
        datetime created_at
    }
    TEACHERS {
        int id PK
        int user_id FK, UK
        string name
        string subject
        string phone
    }
    CLASSES {
        int id PK
        string class_name
        string section
        int teacher_id FK
    }
    STUDENTS {
        int id PK
        int user_id FK, UK
        string name
        int age
        string department
        int class_id FK
        boolean is_representative
    }
    ATTENDANCE {
        int id PK
        int student_id FK
        int class_id FK
        date date
        string status
        int marked_by_id FK
    }
    RESULTS {
        int id PK
        int student_id FK
        string subject
        int marks
        string status
        int marked_by_id FK
    }
    ANNOUNCEMENTS {
        int id PK
        string title
        string content
        int class_id FK
        int created_by_id FK
        string status
        datetime created_at
    }
    MESSAGES {
        int id PK
        int sender_id FK
        int recipient_id FK
        string content
        datetime sent_at
        boolean is_read
    }

    ROLES ||--|{ USERS : "has"
    ROLES ||--|{ ROLE_PERMISSIONS : "associated with"
    PERMISSIONS ||--|{ ROLE_PERMISSIONS : "associated with"
    
    USERS ||--|| TEACHERS : "profile for"
    USERS ||--|| STUDENTS : "profile for"
    
    TEACHERS ||--o{ CLASSES : "manages"
    CLASSES ||--o{ STUDENTS : "contains"
    
    STUDENTS ||--o{ ATTENDANCE : "has records of"
    CLASSES ||--o{ ATTENDANCE : "tracks"
    USERS ||--o{ ATTENDANCE : "marks"
    
    STUDENTS ||--o{ RESULTS : "obtains"
    USERS ||--o{ RESULTS : "records"
    
    CLASSES ||--o{ ANNOUNCEMENTS : "target of"
    USERS ||--o{ ANNOUNCEMENTS : "posts"
    
    USERS ||--o{ MESSAGES : "sends"
    USERS ||--o{ MESSAGES : "receives"
```

## Description of Relations

1. **Roles and Permissions**:
   - **`roles`** and **`permissions`** are linked via the **`role_permissions`** junction table, forming a many-to-many relationship mapping capabilities.
   - **`roles`** has a one-to-many relationship with **`users`** (every user has exactly one role).

2. **User Profiles**:
   - **`users`** has a one-to-one relationship with both **`teachers`** and **`students`**. A user profile can extend into a teacher or student record, with `user_id` acting as a unique key.

3. **Academic Structure**:
   - **`teachers`** has a one-to-many relationship with **`classes`** (each class can have one assigned class teacher).
   - **`classes`** has a one-to-many relationship with **`students`** (each student is registered in one class).

4. **Tracking & Logs**:
   - **`attendance`** joins **`students`**, **`classes`**, and the **`users`** who graded it.
   - **`results`** tracks exam marks for a **`student`**, graded by a specific **`user`** (staff).
   - **`announcements`** has a foreign key to **`classes`** (for class-specific board feeds) and **`users`** (the poster).
   - **`messages`** links sender and recipient user accounts (**`users`**) for direct communication records.
