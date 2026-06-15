from functools import wraps
from flask import session, redirect, url_for, flash, abort, g
from models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        # Load user and check active status
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            flash("Your account has been deactivated or deleted.", "danger")
            return redirect(url_for('auth.login'))
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                flash("Your account is deactivated or deleted.", "danger")
                return redirect(url_for('auth.login'))
            
            if user.role.name not in roles:
                flash("Access Denied: You do not have the required role to access this page.", "danger")
                abort(403)
                
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                flash("Your account is deactivated or deleted.", "danger")
                return redirect(url_for('auth.login'))
            
            if not user.has_permission(permission_name):
                flash(f"Access Denied: Missing permission '{permission_name}'", "danger")
                abort(403)
                
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
