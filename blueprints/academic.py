from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, session
from models import User, Role, Student, Teacher, Class, Result
from database import db
from decorators import login_required, role_required, permission_required

academic_bp = Blueprint('academic', __name__)

# ================= STUDENT CRUD =================

@academic_bp.route('/students')
@login_required
def students_list():
    user = g.current_user
    if user.role.name in ['Principal', 'Teacher']:
        students = Student.query.all()
    elif user.role.name == 'Student Representative' and user.student_profile:
        # Rep can see classmates
        class_id = user.student_profile.class_id
        if class_id:
            students = Student.query.filter_by(class_id=class_id).all()
        else:
            students = []
    else:
        # Standard Student can't see list, redirect to their profile/results
        flash("You are not authorized to view the student list.", "warning")
        return redirect(url_for('academic.student_results', student_id=user.student_profile.id))
        
    return render_template('academic/student_list.html', students=students)

@academic_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def student_add():
    classes = Class.query.all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        age = request.form.get('age', type=int)
        department = request.form.get('department', '').strip()
        class_id = request.form.get('class_id', type=int)
        is_rep = 'is_representative' in request.form

        if not username or not password or not name:
            flash("Username, password and name are required.", "danger")
            return redirect(url_for('academic.student_add'))

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('academic.student_add'))

        # Create user account
        role_name = 'Student Representative' if is_rep else 'Student'
        student_role = Role.query.filter_by(name=role_name).first()
        
        user = User(username=username, role=student_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create student profile
        student = Student(
            user_id=user.id,
            name=name,
            age=age,
            department=department,
            class_id=class_id if class_id != 0 else None,
            is_representative=is_rep
        )
        db.session.add(student)
        db.session.commit()

        flash(f"Student {name} created successfully.", "success")
        return redirect(url_for('academic.students_list'))

    return render_template('academic/student_form.html', classes=classes, title="Add Student")

@academic_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def student_edit(id):
    student = Student.query.get_or_404(id)
    classes = Class.query.all()
    
    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.age = request.form.get('age', type=int)
        student.department = request.form.get('department', '').strip()
        
        class_id = request.form.get('class_id', type=int)
        student.class_id = class_id if class_id != 0 else None
        
        is_rep = 'is_representative' in request.form
        student.is_representative = is_rep
        
        # Update underlying user role
        role_name = 'Student Representative' if is_rep else 'Student'
        student.user.role = Role.query.filter_by(name=role_name).first()
        
        # Option to update password
        password = request.form.get('password', '')
        if password:
            student.user.set_password(password)
            
        db.session.commit()
        flash(f"Student {student.name} updated successfully.", "success")
        return redirect(url_for('academic.students_list'))

    return render_template('academic/student_form.html', student=student, classes=classes, title="Edit Student")

@academic_bp.route('/students/delete/<int:id>')
@login_required
@role_required('Principal')
def student_delete(id):
    student = Student.query.get_or_404(id)
    user = student.user
    db.session.delete(student)
    db.session.delete(user) # Cascaded deletes
    db.session.commit()
    flash("Student deleted successfully.", "success")
    return redirect(url_for('academic.students_list'))


# ================= TEACHER CRUD =================

@academic_bp.route('/teachers')
@login_required
def teachers_list():
    if g.current_user.role.name not in ['Principal', 'Teacher']:
        flash("You are not authorized to view the teacher list.", "warning")
        return redirect(url_for('home'))
    teachers = Teacher.query.all()
    return render_template('academic/teacher_list.html', teachers=teachers)

@academic_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def teacher_add():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        subject = request.form.get('subject', '').strip()
        phone = request.form.get('phone', '').strip()

        if not username or not password or not name:
            flash("Username, password and name are required.", "danger")
            return redirect(url_for('academic.teacher_add'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('academic.teacher_add'))

        teacher_role = Role.query.filter_by(name='Teacher').first()
        user = User(username=username, role=teacher_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        teacher = Teacher(
            user_id=user.id,
            name=name,
            subject=subject,
            phone=phone
        )
        db.session.add(teacher)
        db.session.commit()

        flash(f"Teacher {name} created successfully.", "success")
        return redirect(url_for('academic.teachers_list'))

    return render_template('academic/teacher_form.html', title="Add Teacher")

@academic_bp.route('/teachers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def teacher_edit(id):
    teacher = Teacher.query.get_or_404(id)
    if request.method == 'POST':
        teacher.name = request.form.get('name', '').strip()
        teacher.subject = request.form.get('subject', '').strip()
        teacher.phone = request.form.get('phone', '').strip()

        password = request.form.get('password', '')
        if password:
            teacher.user.set_password(password)

        db.session.commit()
        flash(f"Teacher {teacher.name} updated successfully.", "success")
        return redirect(url_for('academic.teachers_list'))

    return render_template('academic/teacher_form.html', teacher=teacher, title="Edit Teacher")

@academic_bp.route('/teachers/delete/<int:id>')
@login_required
@role_required('Principal')
def teacher_delete(id):
    teacher = Teacher.query.get_or_404(id)
    user = teacher.user
    db.session.delete(teacher)
    db.session.delete(user)
    db.session.commit()
    flash("Teacher deleted successfully.", "success")
    return redirect(url_for('academic.teachers_list'))


# ================= CLASS CRUD =================

@academic_bp.route('/classes')
@login_required
def classes_list():
    user = g.current_user
    if user.role.name in ['Principal', 'Teacher']:
        classes = Class.query.all()
    elif user.student_profile and user.student_profile.class_id:
        classes = Class.query.filter_by(id=user.student_profile.class_id).all()
    else:
        classes = []
    return render_template('academic/class_list.html', classes=classes)

@academic_bp.route('/classes/add', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def class_add():
    teachers = Teacher.query.all()
    if request.method == 'POST':
        class_name = request.form.get('class_name', '').strip()
        section = request.form.get('section', '').strip()
        teacher_id = request.form.get('teacher_id', type=int)

        if not class_name or not section:
            flash("Class name and section are required.", "danger")
            return redirect(url_for('academic.class_add'))

        new_class = Class(
            class_name=class_name,
            section=section,
            teacher_id=teacher_id if teacher_id != 0 else None
        )
        db.session.add(new_class)
        db.session.commit()

        flash(f"Class {class_name}-{section} created successfully.", "success")
        return redirect(url_for('academic.classes_list'))

    return render_template('academic/class_form.html', teachers=teachers, title="Add Class")

@academic_bp.route('/classes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Principal')
def class_edit(id):
    cls = Class.query.get_or_404(id)
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        cls.class_name = request.form.get('class_name', '').strip()
        cls.section = request.form.get('section', '').strip()
        
        teacher_id = request.form.get('teacher_id', type=int)
        cls.teacher_id = teacher_id if teacher_id != 0 else None
        
        db.session.commit()
        flash(f"Class {cls.class_name} updated successfully.", "success")
        return redirect(url_for('academic.classes_list'))

    return render_template('academic/class_form.html', cls=cls, teachers=teachers, title="Edit Class")

@academic_bp.route('/classes/delete/<int:id>')
@login_required
@role_required('Principal')
def class_delete(id):
    cls = Class.query.get_or_404(id)
    db.session.delete(cls)
    db.session.commit()
    flash("Class deleted successfully.", "success")
    return redirect(url_for('academic.classes_list'))


# ================= RESULTS MANAGEMENT =================

@academic_bp.route('/results')
@login_required
def results_list():
    user = g.current_user
    if user.role.name in ['Principal', 'Teacher']:
        results = Result.query.all()
        return render_template('academic/results.html', results=results)
    
    # Standard students and reps are redirected to see only their own results
    if user.student_profile:
        return redirect(url_for('academic.student_results', student_id=user.student_profile.id))
    
    abort(403)

@academic_bp.route('/results/student/<int:student_id>')
@login_required
def student_results(student_id):
    user = g.current_user
    student = Student.query.get_or_404(student_id)
    
    # Access check: Student can only view their own. Rep can only view their own.
    # Teachers and Principals can view any student's results.
    if user.role.name in ['Student', 'Student Representative']:
        if not user.student_profile or user.student_profile.id != student_id:
            flash("Security Restriction: You cannot view other student's academic records.", "danger")
            abort(403)
            
    results = Result.query.filter_by(student_id=student_id).all()
    return render_template('academic/student_results.html', student=student, results=results)

@academic_bp.route('/results/add', methods=['GET', 'POST'])
@login_required
@role_required('Principal', 'Teacher')
def result_add():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        subject = request.form.get('subject', '').strip()
        marks = request.form.get('marks', type=int)

        if not student_id or not subject or marks is None:
            flash("All fields are required.", "danger")
            return redirect(url_for('academic.result_add'))

        status = "Pass" if marks >= 40 else "Fail"
        
        result = Result(
            student_id=student_id,
            subject=subject,
            marks=marks,
            status=status,
            marked_by_id=g.current_user.id
        )
        db.session.add(result)
        db.session.commit()

        flash("Result record saved successfully.", "success")
        return redirect(url_for('academic.results_list'))

    return render_template('academic/result_form.html', students=students, title="Add Result")

@academic_bp.route('/results/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Principal', 'Teacher')
def result_edit(id):
    result = Result.query.get_or_404(id)
    students = Student.query.all()
    
    if request.method == 'POST':
        result.student_id = request.form.get('student_id', type=int)
        result.subject = request.form.get('subject', '').strip()
        result.marks = request.form.get('marks', type=int)
        result.status = "Pass" if result.marks >= 40 else "Fail"
        result.marked_by_id = g.current_user.id
        
        db.session.commit()
        flash("Result record updated successfully.", "success")
        return redirect(url_for('academic.results_list'))

    return render_template('academic/result_form.html', result=result, students=students, title="Edit Result")

@academic_bp.route('/results/delete/<int:id>')
@login_required
@role_required('Principal', 'Teacher')
def result_delete(id):
    result = Result.query.get_or_404(id)
    db.session.delete(result)
    db.session.commit()
    flash("Result record deleted successfully.", "success")
    return redirect(url_for('academic.results_list'))
