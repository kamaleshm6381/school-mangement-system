from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
from datetime import datetime, date
from models import User, Student, Class, Attendance, Teacher
from database import db
from decorators import login_required, role_required

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
@role_required('Principal', 'Teacher')
def mark_attendance():
    # If the user is a teacher, let's find their classes, or show all classes if Principal
    user = g.current_user
    if user.role.name == 'Teacher' and user.teacher_profile:
        classes = Class.query.filter_by(teacher_id=user.teacher_profile.id).all()
    else:
        classes = Class.query.all()

    selected_class_id = request.args.get('class_id', type=int)
    selected_date_str = request.args.get('date', date.today().isoformat())
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    students = []
    existing_attendance = {}
    
    if selected_class_id:
        students = Student.query.filter_by(class_id=selected_class_id).all()
        # Find existing attendance records for this class on this date
        records = Attendance.query.filter_by(class_id=selected_class_id, date=selected_date).all()
        existing_attendance = {r.student_id: r.status for r in records}

    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        date_str = request.form.get('date')
        post_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Verify permissions
        if user.role.name == 'Teacher' and user.teacher_profile:
            cls = Class.query.get(class_id)
            if not cls or cls.teacher_id != user.teacher_profile.id:
                flash("You can only mark attendance for your own classes.", "danger")
                return redirect(url_for('attendance.mark_attendance'))

        students_in_class = Student.query.filter_by(class_id=class_id).all()
        
        for s in students_in_class:
            status = request.form.get(f'status_{s.id}', 'Absent')
            
            # Check if record already exists
            record = Attendance.query.filter_by(student_id=s.id, class_id=class_id, date=post_date).first()
            if record:
                record.status = status
                record.marked_by_id = user.id
            else:
                record = Attendance(
                    student_id=s.id,
                    class_id=class_id,
                    date=post_date,
                    status=status,
                    marked_by_id=user.id
                )
                db.session.add(record)
        
        db.session.commit()
        flash(f"Attendance for class successfully updated for {date_str}.", "success")
        return redirect(url_for('attendance.mark_attendance', class_id=class_id, date=date_str))

    return render_template(
        'attendance/mark.html',
        classes=classes,
        students=students,
        selected_class_id=selected_class_id,
        selected_date_str=selected_date_str,
        existing_attendance=existing_attendance
    )

@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_attendance(student_id):
    user = g.current_user
    student = Student.query.get_or_404(student_id)
    
    # Access checks: Student / Rep can only view their own
    if user.role.name in ['Student', 'Student Representative']:
        if not user.student_profile or user.student_profile.id != student_id:
            flash("Security Restriction: You cannot view attendance details of other students.", "danger")
            abort(403)
            
    records = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).all()
    
    # Calculate percentages
    total_days = len(records)
    present_days = sum(1 for r in records if r.status in ['Present', 'Late'])
    late_days = sum(1 for r in records if r.status == 'Late')
    absent_days = sum(1 for r in records if r.status == 'Absent')
    
    percentage = (present_days / total_days * 100) if total_days > 0 else 100.0

    return render_template(
        'attendance/student_attendance.html',
        student=student,
        records=records,
        total_days=total_days,
        present_days=present_days,
        late_days=late_days,
        absent_days=absent_days,
        percentage=round(percentage, 1)
    )

@attendance_bp.route('/report')
@login_required
def attendance_report():
    user = g.current_user
    # Principal sees all classes, Teacher sees their own, Student Rep sees their class
    if user.role.name == 'Principal':
        classes = Class.query.all()
    elif user.role.name == 'Teacher' and user.teacher_profile:
        classes = Class.query.filter_by(teacher_id=user.teacher_profile.id).all()
    elif user.role.name == 'Student Representative' and user.student_profile:
        classes = Class.query.filter_by(id=user.student_profile.class_id).all()
    else:
        # Standard Student is not allowed
        flash("You are not authorized to view the attendance report.", "warning")
        return redirect(url_for('attendance.student_attendance', student_id=user.student_profile.id))
        
    class_reports = []
    for cls in classes:
        # Get all attendance records for students in this class
        students = Student.query.filter_by(class_id=cls.id).all()
        student_ids = [s.id for s in students]
        
        if student_ids:
            records = Attendance.query.filter(Attendance.student_id.in_(student_ids)).all()
            total = len(records)
            present = sum(1 for r in records if r.status in ['Present', 'Late'])
            percentage = (present / total * 100) if total > 0 else 100.0
        else:
            total = 0
            present = 0
            percentage = 100.0
            
        class_reports.append({
            'class_obj': cls,
            'student_count': len(students),
            'total_marked': total,
            'present_count': present,
            'percentage': round(percentage, 1)
        })
        
    return render_template('attendance/report.html', class_reports=class_reports)
