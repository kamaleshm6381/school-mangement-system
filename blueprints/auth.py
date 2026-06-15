from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from models import User
from database import db
from decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them to dashboard
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact the Principal.", "danger")
                return redirect(url_for('auth.login'))
            
            # Secure session: clear any existing data, then store session keys
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role.name
            
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    # Load profile info based on role
    return render_template('auth/profile.html', user=g.current_user)
