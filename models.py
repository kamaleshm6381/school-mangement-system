from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

# Association Table for Role and Permission (Many-to-Many)
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. Principal, Teacher, Student Representative, Student
    description = db.Column(db.String(255))
    
    # Relationships
    users = db.relationship('User', backref='role', lazy=True)
    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))

    def __repr__(self):
        return f"<Role {self.name}>"

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. manage_users, mark_attendance, view_results, publish_announcements
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Permission {self.name}>"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Back-references for Teacher/Student profiles (One-to-One)
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm_name):
        return any(p.name == perm_name for p in self.role.permissions)

    def __repr__(self):
        return f"<User {self.username} ({self.role.name})>"

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    # Relationships
    classes = db.relationship('Class', backref='teacher', lazy=True)

    def __repr__(self):
        return f"<Teacher {self.name}>"

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    department = db.Column(db.String(100))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    is_representative = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', cascade="all, delete-orphan", lazy=True)
    results = db.relationship('Result', backref='student', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Student {self.name}>"

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    students = db.relationship('Student', backref='class_', lazy=True)
    announcements = db.relationship('Announcement', backref='class_', cascade="all, delete-orphan", lazy=True)
    attendance_records = db.relationship('Attendance', backref='class_', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"{self.class_name} - {self.section}"

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'Present', 'Absent', 'Late'
    marked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    marked_by = db.relationship('User', backref='marked_attendance', lazy=True)

    def __repr__(self):
        return f"<Attendance student_id={self.student_id} date={self.date} status={self.status}>"

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'Pass', 'Fail'
    marked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    marked_by = db.relationship('User', backref='uploaded_results', lazy=True)

    def __repr__(self):
        return f"<Result student_id={self.student_id} subject={self.subject} marks={self.marks}>"

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='CASCADE'), nullable=True) # Null for global announcements
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='Approved', nullable=False) # 'Draft', 'Pending', 'Approved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_by = db.relationship('User', backref='announcements', lazy=True)

    def __repr__(self):
        return f"<Announcement title={self.title} status={self.status}>"

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships with primaryjoin specified due to dual foreign keys to users table
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy='dynamic'))

    def __repr__(self):
        return f"<Message sender={self.sender_id} recipient={self.recipient_id} sent_at={self.sent_at}>"
