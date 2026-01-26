from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, DateField, TimeField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select'),
        ('Cooking', 'Cooking'),
        ('Craft', 'Craft'),
        ('Technology', 'Technology'),
        ('Environmental', 'Environmental'),
        ('Fitness', 'Fitness'),
        ('Music', 'Music'),
        ('Outdoor', 'Outdoor'),
        ('Social', 'Social'),
        ('Art', 'Art'),
        ('Others', 'Others')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    slots = IntegerField('Slots', validators=[DataRequired(), NumberRange(min=1)])
    image = FileField('Event Image (optional)', validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Images only')])
    submit = SubmitField('Create')

class ReflectionForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comments = TextAreaField('Comments', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit')

class CreatorReflectionForm(FlaskForm):
    rating = IntegerField('Overall Event Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comments = TextAreaField('Organizer Notes / Lessons Learned', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Submit Reflection')

class StoryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=5000)])
    date = DateField('Date', validators=[Optional()])
    media = FileField('Upload Media', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'], 'Images and videos only')])
    voice_recording = StringField('Voice Recording', validators=[Optional()])
    tags = StringField('Tags', validators=[Optional()])
    custom_tags = StringField('Custom Tags', validators=[Optional()])
    privacy = SelectField('Privacy', choices=[('Public', 'Public'), ('Friends', 'Friends'), ('Private', 'Private')], validators=[DataRequired()])
    submit = SubmitField('Post')

class ChatForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')