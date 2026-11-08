from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Register As', choices=[('customer', 'Customer'), ('staff', 'Sales Staff')], default='customer')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    supplier_id = SelectField('Supplier (Optional)', coerce=int, validators=[Optional()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    min_stock_alert = IntegerField('Low Stock Threshold', default=10, validators=[DataRequired(), NumberRange(min=1)])
    cover_image = FileField('Cover Image (Upload)', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only! (png, jpg, jpeg, gif, webp)')
    ])
    description = TextAreaField('Description')
    submit = SubmitField('Save Book')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description (Optional)')
    submit = SubmitField('Save Category')

class SupplierForm(FlaskForm):
    name = StringField('Supplier / Publisher Name', validators=[DataRequired(), Length(max=150)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Supplier')

class StaffCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('staff', 'Sales Staff / Cashier'), ('manager', 'Store Manager'), ('admin', 'System Administrator')], default='staff')
    submit = SubmitField('Create Account')

class CartAddForm(FlaskForm):
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to Cart')

class POSCheckoutForm(FlaskForm):
    customer_name = StringField('Customer Name / ID', validators=[DataRequired()])
    customer_phone = StringField('Customer Phone (Optional)', validators=[Optional()])
    discount_pct = FloatField('Discount (%)', default=0.0, validators=[NumberRange(min=0, max=100)])
    tax_pct = FloatField('Tax / GST (%)', default=5.0, validators=[NumberRange(min=0, max=50)])
    payment_method = SelectField('Payment Method', choices=[('Cash', 'Cash'), ('Card', 'Debit/Credit Card'), ('UPI', 'UPI / QR Code')], default='Cash')
    submit = SubmitField('Generate Bill & Complete Sale')

class ReturnForm(FlaskForm):
    invoice_no = StringField('Invoice Number (e.g. INV-20261107-1234)', validators=[DataRequired()])
    quantity = IntegerField('Quantity to Return', default=1, validators=[DataRequired(), NumberRange(min=1)])
    reason = TextAreaField('Reason for Return', validators=[DataRequired()])
    submit = SubmitField('Process Return')
