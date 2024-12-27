from flask import Blueprint, render_template, redirect, url_for, flash
from app.forms import RegistrationForm, LoginForm
from app.database.models import User
from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash

home_bp = Blueprint('home', __name__)

@home_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('home.login'))
    return render_template('register.html', form=form)

@home_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            flash('Login successful!', 'success')
            return redirect(url_for('home.home'))  # Redirect to home or dashboard
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', form=form)

@home_bp.route('/')
def home():
    """Render the home page."""
    return render_template('home.html')  # Render the home page

