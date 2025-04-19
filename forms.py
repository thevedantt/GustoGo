from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, HiddenField
from wtforms import SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User
from flask_login import current_user
from config import CAKE_FLAVORS, CAKE_SIZES, CAKE_FROSTINGS, CAKE_TOPPINGS

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_phone(self, phone):
        if not phone.data.isdigit():
            raise ValidationError('Phone number must contain only digits.')
        if len(phone.data) < 10 or len(phone.data) > 15:
            raise ValidationError('Phone number must be between 10 and 15 digits.')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Update Profile')
    
    def validate_phone(self, phone):
        if not phone.data.isdigit():
            raise ValidationError('Phone number must contain only digits.')
        if len(phone.data) < 10 or len(phone.data) > 15:
            raise ValidationError('Phone number must be between 10 and 15 digits.')
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if kwargs.get('obj'):
            user = kwargs['obj']
            if user.username:
                name_parts = user.username.split()
                self.first_name.data = name_parts[0] if name_parts else ''
                self.last_name.data = name_parts[1] if len(name_parts) > 1 else ''

class CakeCustomizationForm(FlaskForm):
    flavor = SelectField('Cake Flavor', validators=[DataRequired()], choices=[(f['id'], f['name']) for f in CAKE_FLAVORS])
    size = SelectField('Cake Size', validators=[DataRequired()], choices=[(s['id'], s['name']) for s in CAKE_SIZES])
    frosting = SelectField('Frosting', validators=[DataRequired()], choices=[(f['id'], f['name']) for f in CAKE_FROSTINGS])
    topping = SelectField('Topping', validators=[DataRequired()], choices=[(t['id'], t['name']) for t in CAKE_TOPPINGS])
    message = StringField('Special Message (Optional)', validators=[Optional(), Length(max=100)])
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired()])
    submit = SubmitField('Add to Cart')

class CartUpdateForm(FlaskForm):
    item_id = HiddenField('Item ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Update')

class CheckoutForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    stripe_token = HiddenField()
    upi_id = StringField('UPI ID')
    payment_method = StringField('Payment Method', validators=[DataRequired()])
    
    def validate_phone(self, phone):
        if not phone.data.isdigit():
            raise ValidationError('Phone number must contain only digits.')
        if len(phone.data) < 10 or len(phone.data) > 15:
            raise ValidationError('Phone number must be between 10 and 15 digits.')
    
    def validate_email(self, email):
        if current_user.is_authenticated and email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different one.')
    
    def __init__(self, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Pre-fill form with user data
            self.first_name.data = current_user.first_name
            self.last_name.data = current_user.last_name
            self.email.data = current_user.email
            self.phone.data = current_user.phone
            self.address.data = current_user.address
