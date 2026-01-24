from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf.file import FileField, FileAllowed

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
        ('Others', 'Others')   # <-- added Others category
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
    # separate form for creators (different labels/helptext) but same storage model
    rating = IntegerField('Overall Event Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comments = TextAreaField('Organizer Notes / Lessons Learned', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Submit Reflection')