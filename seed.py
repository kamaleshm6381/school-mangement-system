import datetime
from app import create_app
from database import db
from models import Role, Permission, User, Teacher, Student, Class, Attendance, Result, Announcement

def seed_database():
    app = create_app()
    with app.app_context():
        # Recreate all tables
        db.drop_all()
        db.create_all()
        print("Database tables recreated.")

        # 1. Create Permissions
        permissions_list = [
            # User & Class management
            ('manage_users', 'Can create, read, update, delete all users'),
            ('manage_classes', 'Can create, read, update, delete academic classes'),
            # Attendance
            ('mark_attendance', 'Can mark student daily attendance'),
            ('view_attendance_reports', 'Can view general class or school attendance reports'),
            # Results
            ('manage_results', 'Can upload, update and delete academic marks'),
            # Announcements
            ('create_announcement', 'Can draft or publish school/class announcements'),
            ('approve_announcement', 'Can approve pending drafts of announcements'),
            # Messaging
            ('send_messages', 'Can send messages to other users')
        ]

        db_perms = {}
        for name, desc in permissions_list:
            perm = Permission(name=name, description=desc)
            db.session.add(perm)
            db_perms[name] = perm
        db.session.commit()
        print("Permissions seeded.")

        # 2. Create Roles
        roles_data = {
            'Principal': {
                'desc': 'School Administrator with complete system-wide access',
                'perms': ['manage_users', 'manage_classes', 'view_attendance_reports', 'manage_results', 'create_announcement', 'approve_announcement', 'send_messages']
            },
            'Teacher': {
                'desc': 'Academic staff member managing student classes, attendance, and results',
                'perms': ['mark_attendance', 'view_attendance_reports', 'manage_results', 'create_announcement', 'send_messages']
            },
            'Student Representative': {
                'desc': 'Class leader student with access to class attendance summaries and announcement drafts',
                'perms': ['view_attendance_reports', 'create_announcement', 'send_messages']
            },
            'Student': {
                'desc': 'Standard student with personal academic progress views',
                'perms': ['send_messages']
            }
        }

        db_roles = {}
        for role_name, details in roles_data.items():
            role = Role(name=role_name, description=details['desc'])
            for p_name in details['perms']:
                role.permissions.append(db_perms[p_name])
            db.session.add(role)
            db_roles[role_name] = role
        db.session.commit()
        print("Roles and Role-Permission mappings seeded.")

        # 3. Create Users & Profiles
        
        # Principal
        principal_user = User(username='principal', role=db_roles['Principal'])
        principal_user.set_password('password123')
        db.session.add(principal_user)

        # Teachers
        teachers_data = [
            ('teacher1', 'Dr. UMAMAHESWARI', 'Mathematics', '+91-9876543210'),
            ('SARO', 'SAROJINI', 'Science', '+91-9876543211'),
            ('teacher2', 'Mr. Walter White', 'Chemistry', '+1-505-124-5678'),
            ('teacher3', 'Ms. Minerva McGonagall', 'English', '+44-20-7946-0192'),
            ('teacher4', 'Dr. Bruce Banner', 'Physics', '+1-703-555-0145')
        ]
        
        db_teachers = []
        for username, name, subject, phone in teachers_data:
            t_user = User(username=username, role=db_roles['Teacher'])
            t_user.set_password('password123')
            db.session.add(t_user)
            db.session.commit() # commit to get user.id
            
            t_profile = Teacher(user_id=t_user.id, name=name, subject=subject, phone=phone)
            db.session.add(t_profile)
            db_teachers.append(t_profile)
        
        db.session.commit()
        print("Teachers profiles created.")

        # 4. Create Classes
        classes_data = [
            ('Grade 10 Mathematics', 'A', db_teachers[0].id), # Dr. UMAMAHESWARI
            ('11 TH SCIENCE', 'A', db_teachers[1].id),       # SAROJINI
            ('Grade 11 Chemistry', 'A', db_teachers[2].id),   # Walter White
            ('Grade 12 English', 'B', db_teachers[3].id),     # Minerva McGonagall
            ('Grade 11 Physics', 'A', db_teachers[4].id)      # Bruce Banner
        ]
        
        db_classes = []
        for class_name, section, teacher_id in classes_data:
            cls = Class(class_name=class_name, section=section, teacher_id=teacher_id)
            db.session.add(cls)
            db.session.commit() # commit to get cls.id
            db_classes.append(cls)
            
        print("Classes created.")

        # 5. Create Students & Student Reps
        students_data = [
            # Class 0: Grade 10 Mathematics A
            ('kamaleshwaran', 'kamaleshwaran S', 21, 'Mathematics', db_classes[0].id, True),
            ('kamalesh', 'kamalesh M', 21, 'Mathematics', db_classes[0].id, False),
            ('student1', 'Timmy Vance', 15, 'Mathematics', db_classes[0].id, False),
            ('student2', 'Bobby Drake', 15, 'Mathematics', db_classes[0].id, False),
            ('student3', 'Kitty Pryde', 15, 'Mathematics', db_classes[0].id, False),
            
            # Class 1: 11 TH SCIENCE A
            ('student_rep_science', 'John Connor', 16, 'Science', db_classes[1].id, True),
            ('student_sci1', 'Sarah Connor', 16, 'Science', db_classes[1].id, False),
            ('student_sci2', 'T-800', 17, 'Science', db_classes[1].id, False),
            
            # Class 2: Grade 11 Chemistry A
            ('classleader2', 'Jesse Pinkman', 17, 'Science', db_classes[2].id, True),
            ('student4', 'Jane Margolis', 17, 'Science', db_classes[2].id, False),
            ('student5', 'Badger Mayhew', 17, 'Science', db_classes[2].id, False),
            
            # Class 3: Grade 12 English B
            ('classleader3', 'Hermione Granger', 18, 'Arts', db_classes[3].id, True),
            ('student6', 'Harry Potter', 18, 'Arts', db_classes[3].id, False),
            ('student7', 'Ron Weasley', 18, 'Arts', db_classes[3].id, False),
            
            # Class 4: Grade 11 Physics A
            ('classleader4', 'Peter Parker', 17, 'Science', db_classes[4].id, True),
            ('student8', 'Gwen Stacy', 17, 'Science', db_classes[4].id, False),
            ('student9', 'Miles Morales', 16, 'Science', db_classes[4].id, False)
        ]
        
        db_students = []
        for username, name, age, dept, class_id, is_rep in students_data:
            role_name = 'Student Representative' if is_rep else 'Student'
            s_user = User(username=username, role=db_roles[role_name])
            s_user.set_password('password123')
            db.session.add(s_user)
            db.session.commit()
            
            s_profile = Student(
                user_id=s_user.id,
                name=name,
                age=age,
                department=dept,
                class_id=class_id,
                is_representative=is_rep
            )
            db.session.add(s_profile)
            db.session.commit()
            db_students.append(s_profile)
            
        print("Student Profiles created.")

        # 6. Create Attendance Records
        today = datetime.date.today()
        days = [today - datetime.timedelta(days=i) for i in range(5)]
        
        teacher1_user = User.query.filter_by(username='teacher1').first()
        teacher1_user_id = teacher1_user.id if teacher1_user else 1
        
        count = 0
        for s in db_students:
            for day in days:
                status = 'Present'
                if s.name == 'Timmy Vance' and day == days[1]:
                    status = 'Absent'
                elif s.name == 'kamalesh M' and day == days[2]:
                    status = 'Late'
                elif s.name == 'Jesse Pinkman' and day == days[0]:
                    status = 'Absent'
                elif s.name == 'Harry Potter' and day == days[3]:
                    status = 'Absent'
                
                att = Attendance(
                    student_id=s.id,
                    class_id=s.class_id,
                    date=day,
                    status=status,
                    marked_by_id=teacher1_user_id
                )
                db.session.add(att)
                count += 1
        db.session.commit()
        print(f"Seeded {count} attendance records.")

        # 7. Create Result Records (Grades)
        marks_data = [
            # kamaleshwaran S
            ('kamaleshwaran S', 'Mathematics', 85),
            ('kamaleshwaran S', 'Science', 78),
            # kamalesh M
            ('kamalesh M', 'Mathematics', 92),
            ('kamalesh M', 'Science', 81),
            # Timmy Vance
            ('Timmy Vance', 'Mathematics', 45),
            ('Timmy Vance', 'Science', 52),
            # John Connor
            ('John Connor', 'Science', 70),
            ('John Connor', 'Mathematics', 65),
            # Jesse Pinkman
            ('Jesse Pinkman', 'Chemistry', 55),
            ('Jesse Pinkman', 'Mathematics', 38),
            # Hermione Granger
            ('Hermione Granger', 'English', 99),
            ('Hermione Granger', 'Mathematics', 98),
            # Harry Potter
            ('Harry Potter', 'English', 75),
            ('Harry Potter', 'Mathematics', 62),
            # Peter Parker
            ('Peter Parker', 'Physics', 95),
            ('Peter Parker', 'Mathematics', 88)
        ]
        
        res_count = 0
        for name, subject, marks in marks_data:
            student = Student.query.filter_by(name=name).first()
            if student:
                status = 'Pass' if marks >= 40 else 'Fail'
                res = Result(
                    student_id=student.id,
                    subject=subject,
                    marks=marks,
                    status=status,
                    marked_by_id=teacher1_user_id
                )
                db.session.add(res)
                res_count += 1
        db.session.commit()
        print(f"Seeded {res_count} academic result records.")

        # 8. Create Announcements
        principal_db_user = User.query.filter_by(username='principal').first()
        principal_id = principal_db_user.id if principal_db_user else 1
        
        announcements = [
            Announcement(
                title='Welcome to Soma Velas Primary School Portal!',
                content='We are thrilled to launch our new glassmorphic school management portal. Here you can track classes, attendance records, academic performance grades, and coordinate announcements. Let us have an excellent semester!',
                class_id=None,
                created_by_id=principal_id,
                status='Approved'
            ),
            Announcement(
                title='Annual Sports Day 2026 - Registration Open',
                content='The Annual Sports Day is scheduled for next month. Interested students should contact their respective class representative or class teacher to register for events by Friday.',
                class_id=None,
                created_by_id=principal_id,
                status='Approved'
            ),
            Announcement(
                title='Mathematics Mid-Term Exam Announcement',
                content='Please note that the Mathematics Mid-Term exam will be held next Monday at 9:00 AM. Covers chapters 1 to 5. Bring your calculators.',
                class_id=db_classes[0].id,
                created_by_id=db_teachers[0].user_id,
                status='Approved'
            ),
            Announcement(
                title='Chemistry Lab Equipment Check',
                content='Before Thursday lab session, please read pages 45-50 of your lab manual. We will be conducting a titration experiment. Lab coats and safety goggles are mandatory.',
                class_id=db_classes[2].id,
                created_by_id=db_teachers[2].user_id,
                status='Approved'
            ),
            Announcement(
                title='Class Field Trip Proposal to Science Museum',
                content='We would like to propose a class field trip to the local Science Museum next Friday afternoon. I have collected interest signatures from the class.',
                class_id=db_classes[0].id,
                created_by_id=db_students[0].user_id,
                status='Pending'
            )
        ]
        
        for ann in announcements:
            db.session.add(ann)
        db.session.commit()
        print("Seeded announcements.")
        
        print("Database seeding completed successfully with rich manual/demo data!")

if __name__ == '__main__':
    seed_database()
