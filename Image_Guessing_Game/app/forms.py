from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FormField, TextAreaField, FileField
from wtforms.fields.html5 import DateField

class LoginForm(FlaskForm):
    username = StringField('Username', render_kw={'placeholder': 'Username'})
    password = PasswordField('Password', render_kw={'placeholder': 'Password'})
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', render_kw={'placeholder': 'Username'})
    password = PasswordField('Password', render_kw={'placeholder': 'Password'})
    confirm_password = PasswordField('Confirm Password', render_kw={'placeholder': 'Confirm Password'})
    submit = SubmitField('Sign Up')

class IndexForm(FlaskForm):
    login = FormField(LoginForm)
    register = FormField(RegisterForm)

class DashboardForm(FlaskForm):
    # Multiplayer forms
    new_game_proposer_multiPlayer = SubmitField('New game as proposer')
    new_game_guesser_multiPlayer = SubmitField('New Game guesser')

    # Singleplayer forms
    new_game_proposer_singlePlayer = SubmitField('New game as proposer')
    new_game_guesser_singlePlayer = SubmitField('New Game guesser')

    # AI forms
    new_game_guesser_ai = SubmitField('New Game guesser')
