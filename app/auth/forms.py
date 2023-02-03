
from quart_wtf import QuartForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, EqualTo

from app.models import User


class LoginForm(QuartForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(QuartForm):
    login = StringField('Login', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    async def async_validate_login(self, login):
        print('async validate login CALLED')
        user = await User.get_by_login(login.data)
        if user is not None:
            raise ValidationError('Please use a different username.')


class ChangePasswordForm(QuartForm):
    pass
