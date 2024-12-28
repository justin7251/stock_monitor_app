from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.database.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
        validators=[
            DataRequired(),
            Length(min=2, max=20, message="Username must be between 2 and 20 characters")
        ])
    password = PasswordField('Password', 
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long")
        ])
    confirm_password = PasswordField('Confirm Password', 
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ])
    submit = SubmitField('Register')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username',
        validators=[DataRequired()])
    password = PasswordField('Password',
        validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
