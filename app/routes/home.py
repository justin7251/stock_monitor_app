from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import LoginForm, RegistrationForm
from app.database.models import User
from app.database import db
import logging

home_bp = Blueprint('home', __name__)

@home_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    
    form = RegistrationForm()
    
    try:
        if form.validate_on_submit():
            # Log form data for debugging
            logging.info(f"Form submitted with username: {form.username.data}")
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
                return render_template('register.html', title='Register', form=form)

            # Create new user
            hashed_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256'
            )
            
            new_user = User(
                username=form.username.data,
                password=hashed_password
            )

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('home.login'))
            
            except Exception as e:
                db.session.rollback()
                logging.error(f"Database error: {str(e)}")
                flash('An error occurred while registering. Please try again.', 'danger')
                return render_template('register.html', title='Register', form=form)

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
    
    return render_template('register.html', title='Register', form=form)

@home_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
            else:
                flash('Login unsuccessful. Please check username and password.', 'danger')
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@home_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))

@home_bp.route('/')
def index():
    return render_template('home.html')

