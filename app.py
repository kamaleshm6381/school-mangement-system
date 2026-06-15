from flask import Flask, render_template, session, redirect, url_for, g
from config import Config
from database import db
from models import User, Announcement

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.academic import academic_bp
    from blueprints.attendance import attendance_bp
    from blueprints.announcements import announcements_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(academic_bp, url_prefix='/academic')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(announcements_bp, url_prefix='/announcements')

    # Default redirects and dashboard
    @app.route('/')
    def root():
        if 'user_id' in session:
            return redirect(url_for('home'))
        return redirect(url_for('auth.login'))

    @app.route('/home')
    def home():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Import models inside the route to avoid circular dependency
        from models import Student, Teacher, Class, Attendance
        
        # Base dashboard data
        stats = {
            'students': 0,
            'teachers': 0,
            'classes': 0,
            'attendance_pct': 100.0,
            'pending_announcements': 0
        }
        
        if user.role.name == 'Principal':
            stats['students'] = Student.query.count()
            stats['teachers'] = Teacher.query.count()
            stats['classes'] = Class.query.count()
            stats['pending_announcements'] = Announcement.query.filter_by(status='Pending').count()
        elif user.role.name == 'Teacher':
            stats['students'] = Student.query.count()
            stats['classes'] = Class.query.count()
            if user.teacher_profile:
                # Get teacher's pending class announcements approvals
                my_classes = Class.query.filter_by(teacher_id=user.teacher_profile.id).all()
                c_ids = [c.id for c in my_classes]
                if c_ids:
                    stats['pending_announcements'] = Announcement.query.filter(
                        Announcement.status == 'Pending',
                        Announcement.class_id.in_(c_ids)
                    ).count()
        elif user.role.name in ['Student', 'Student Representative'] and user.student_profile:
            # Calculate attendance percentage
            records = Attendance.query.filter_by(student_id=user.student_profile.id).all()
            total_days = len(records)
            present_days = sum(1 for r in records if r.status in ['Present', 'Late'])
            stats['attendance_pct'] = round((present_days / total_days * 100), 1) if total_days > 0 else 100.0
        
        # Load announcements
        if user.role.name in ['Principal', 'Teacher']:
            announcements = Announcement.query.filter_by(status='Approved').order_by(Announcement.created_at.desc()).all()
        else:
            class_id = user.student_profile.class_id if user.student_profile else None
            announcements = Announcement.query.filter(
                Announcement.status == 'Approved',
                db.or_(Announcement.class_id == None, Announcement.class_id == class_id)
            ).order_by(Announcement.created_at.desc()).all()

        return render_template('dashboard.html', user=user, announcements=announcements, stats=stats)

    # Handle unauthorized and not found
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = db.session.get(User, user_id)
            # In case the user is inactive or deleted
            if g.user and not g.user.is_active:
                session.clear()
                g.user = None

    @app.context_processor
    def inject_user_permissions():
        return dict(
            current_user=g.get('user', None),
            has_permission=lambda perm: g.user.has_permission(perm) if g.user else False
        )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)