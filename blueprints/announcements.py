from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
from models import Announcement, Class, User, Role
from database import db
from decorators import login_required, role_required, permission_required

announcements_bp = Blueprint('announcements', __name__)

@announcements_bp.route('/')
@login_required
def list_announcements():
    user = g.current_user
    
    # Base query for approved announcements
    query = Announcement.query.filter_by(status='Approved')
    
    # Filter by user class if they are student/representative
    if user.role.name in ['Student', 'Student Representative']:
        class_id = user.student_profile.class_id if user.student_profile else None
        # View global announcements OR announcements matching their class
        announcements = query.filter(
            db.or_(Announcement.class_id == None, Announcement.class_id == class_id)
        ).order_by(Announcement.created_at.desc()).all()
    else:
        # Principal and Teacher can see all approved announcements
        announcements = query.order_by(Announcement.created_at.desc()).all()
        
    return render_template('announcements/list.html', announcements=announcements)

@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_announcement():
    user = g.current_user
    
    # Check if role has create permission
    if not user.has_permission('create_announcement'):
        flash("You are not authorized to create announcements.", "danger")
        abort(403)
        
    # Get eligible classes
    if user.role.name == 'Principal':
        classes = Class.query.all()
    elif user.role.name == 'Teacher' and user.teacher_profile:
        classes = Class.query.filter_by(teacher_id=user.teacher_profile.id).all()
    elif user.role.name == 'Student Representative' and user.student_profile:
        classes = Class.query.filter_by(id=user.student_profile.class_id).all()
    else:
        classes = []

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        class_id_val = request.form.get('class_id')
        
        class_id = None
        if class_id_val and class_id_val != 'global':
            class_id = int(class_id_val)

        if not title or not content:
            flash("Title and Content are required.", "danger")
            return redirect(url_for('announcements.create_announcement'))

        # Set status based on approval workflow:
        # - Principal: Auto-approved
        # - Teacher: Auto-approved for their own class, but Pending for Global
        # - Student Representative: Always Pending approval
        if user.role.name == 'Principal':
            status = 'Approved'
        elif user.role.name == 'Teacher':
            if class_id is not None:
                # verify it's their class
                cls = Class.query.get(class_id)
                if cls and cls.teacher_id == user.teacher_profile.id:
                    status = 'Approved'
                else:
                    status = 'Pending'
            else:
                # Global announcement from teacher requires Principal approval
                status = 'Pending'
        else: # Student Representative
            status = 'Pending'

        announcement = Announcement(
            title=title,
            content=content,
            class_id=class_id,
            created_by_id=user.id,
            status=status
        )
        db.session.add(announcement)
        db.session.commit()

        if status == 'Approved':
            flash("Announcement published successfully!", "success")
        else:
            flash("Announcement submitted successfully and is pending approval.", "info")
            
        return redirect(url_for('announcements.list_announcements'))

    return render_template('announcements/create.html', classes=classes)

@announcements_bp.route('/manage')
@login_required
@role_required('Principal', 'Teacher')
def manage_announcements():
    user = g.current_user
    
    if user.role.name == 'Principal':
        # Principal can approve any pending announcement
        pending = Announcement.query.filter_by(status='Pending').order_by(Announcement.created_at.desc()).all()
        my_announcements = Announcement.query.filter_by(created_by_id=user.id).all()
    else: # Teacher
        # Teacher can approve pending announcements in classes they teach
        my_classes = Class.query.filter_by(teacher_id=user.teacher_profile.id).all()
        class_ids = [c.id for c in my_classes]
        
        if class_ids:
            pending = Announcement.query.filter(
                Announcement.status == 'Pending',
                Announcement.class_id.in_(class_ids)
            ).order_by(Announcement.created_at.desc()).all()
        else:
            pending = []
            
        my_announcements = Announcement.query.filter_by(created_by_id=user.id).all()

    return render_template('announcements/manage.html', pending=pending, my_announcements=my_announcements)

@announcements_bp.route('/approve/<int:id>')
@login_required
@role_required('Principal', 'Teacher')
def approve_announcement(id):
    user = g.current_user
    announcement = Announcement.query.get_or_404(id)
    
    # Security check: Teacher can only approve announcements for their class
    if user.role.name == 'Teacher':
        if not announcement.class_id:
            flash("Security Restriction: Only the Principal can approve global announcements.", "danger")
            abort(403)
        cls = Class.query.get(announcement.class_id)
        if not cls or cls.teacher_id != user.teacher_profile.id:
            flash("Security Restriction: You can only approve announcements for your class.", "danger")
            abort(403)
            
    announcement.status = 'Approved'
    db.session.commit()
    flash(f"Announcement '{announcement.title}' approved successfully.", "success")
    return redirect(url_for('announcements.manage_announcements'))

@announcements_bp.route('/delete/<int:id>')
@login_required
def delete_announcement(id):
    user = g.current_user
    announcement = Announcement.query.get_or_404(id)
    
    # Principal can delete any announcement.
    # Teacher can delete theirs or pending in their class.
    # Owner can delete theirs if it's pending.
    allowed = False
    if user.role.name == 'Principal':
        allowed = True
    elif user.role.name == 'Teacher':
        if announcement.created_by_id == user.id:
            allowed = True
        elif announcement.class_id:
            cls = Class.query.get(announcement.class_id)
            if cls and cls.teacher_id == user.teacher_profile.id:
                allowed = True
    elif announcement.created_by_id == user.id and announcement.status == 'Pending':
        allowed = True

    if not allowed:
        flash("You are not authorized to delete this announcement.", "danger")
        abort(403)

    db.session.delete(announcement)
    db.session.commit()
    flash("Announcement deleted successfully.", "success")
    return redirect(url_for('announcements.manage_announcements') if user.role.name in ['Principal', 'Teacher'] else url_for('announcements.list_announcements'))
