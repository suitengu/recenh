from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class UsernameForm(FlaskForm):
    username = StringField('LastFM Username', validators=[DataRequired()])
    submit = SubmitField('Check')
