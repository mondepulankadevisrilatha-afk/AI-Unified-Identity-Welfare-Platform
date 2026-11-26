"""WTForms definitions. CSRF protection is provided automatically by
FlaskForm (via Flask-WTF / CSRFProtect).
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, BooleanField, IntegerField, SelectField,
    TextAreaField, DateField, SubmitField,
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, NumberRange, URL,
)

from config import Config


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField("Full name", validators=[Optional(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", "Passwords must match")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    identifier = StringField("Email or username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[Optional(), Length(max=120)])
    age = IntegerField("Age", validators=[Optional(), NumberRange(0, 120)])
    gender = SelectField("Gender", choices=[("", "Select")] +
                         [(g, g) for g in Config.GENDERS], validators=[Optional()])
    annual_income = IntegerField("Annual income (INR)",
                                 validators=[Optional(), NumberRange(0, 100_000_000)])
    social_category = SelectField(
        "Social category",
        choices=[("", "Select")] + [(c, c) for c in Config.CATEGORIES_SOCIAL],
        validators=[Optional()],
    )
    occupation = StringField("Occupation", validators=[Optional(), Length(max=80)])
    state = StringField("State", validators=[Optional(), Length(max=80)])
    is_student = BooleanField("I am a student")
    is_farmer = BooleanField("I am a farmer")
    is_differently_abled = BooleanField("I am differently abled")
    submit = SubmitField("Save profile")


class DocumentUploadForm(FlaskForm):
    document_name = StringField("Document name", validators=[DataRequired(), Length(max=150)])
    category = SelectField("Category", choices=[(c, c) for c in Config.DOCUMENT_CATEGORIES],
                           validators=[DataRequired()])
    file = FileField("File (PDF / PNG / JPG, max 5 MB)", validators=[
        FileRequired(),
        FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image files only."),
    ])
    submit = SubmitField("Upload")


class DocumentReplaceForm(FlaskForm):
    file = FileField("Replacement file", validators=[
        FileRequired(),
        FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image files only."),
    ])
    submit = SubmitField("Replace file")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", "Passwords must match")],
    )
    submit = SubmitField("Change password")


class EligibilityForm(FlaskForm):
    """Manual eligibility check — pre-filled from profile but editable."""
    scheme_id = SelectField("Scheme", coerce=int, validators=[DataRequired()])
    age = IntegerField("Age", validators=[Optional(), NumberRange(0, 120)])
    gender = SelectField("Gender", choices=[("", "Select")] +
                         [(g, g) for g in Config.GENDERS], validators=[Optional()])
    annual_income = IntegerField("Annual income (INR)",
                                 validators=[Optional(), NumberRange(0, 100_000_000)])
    social_category = SelectField(
        "Social category",
        choices=[("", "Select")] + [(c, c) for c in Config.CATEGORIES_SOCIAL],
        validators=[Optional()],
    )
    occupation = StringField("Occupation", validators=[Optional(), Length(max=80)])
    state = StringField("State", validators=[Optional(), Length(max=80)])
    is_student = BooleanField("Student")
    is_farmer = BooleanField("Farmer")
    is_differently_abled = BooleanField("Differently abled")
    submit = SubmitField("Check eligibility")


class ApplicationForm(FlaskForm):
    scheme_id = SelectField("Scheme", coerce=int, validators=[DataRequired()])
    status = SelectField("Status", choices=[(s, s) for s in Config.APPLICATION_STATUSES],
                         validators=[DataRequired()])
    reference_number = StringField("Reference number", validators=[Optional(), Length(max=80)])
    submitted_on = DateField("Submitted on", validators=[Optional()])
    reminder_date = DateField("Reminder date", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save application")


class ChecklistItemForm(FlaskForm):
    item = StringField("Checklist item", validators=[DataRequired(), Length(max=150)])
    submit = SubmitField("Add item")


# -------------------- Admin forms --------------------
class SchemeForm(FlaskForm):
    scheme_name = StringField("Scheme name", validators=[DataRequired(), Length(max=150)])
    category = SelectField("Category", choices=[(c, c) for c in Config.SCHEME_CATEGORIES],
                           validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    benefits = TextAreaField("Benefits", validators=[Optional()])
    official_url = StringField("Official URL", validators=[Optional(), URL(), Length(max=255)])
    required_documents = StringField("Required documents (comma separated)",
                                     validators=[Optional(), Length(max=500)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save scheme")


class RuleForm(FlaskForm):
    field = SelectField("Field", choices=[
        ("age", "Age"),
        ("annual_income", "Annual income"),
        ("gender", "Gender"),
        ("social_category", "Social category"),
        ("occupation", "Occupation"),
        ("state", "State"),
        ("is_student", "Is student"),
        ("is_farmer", "Is farmer"),
        ("is_differently_abled", "Is differently abled"),
    ], validators=[DataRequired()])
    operator = SelectField("Operator", choices=[
        ("<=", "at most (<=)"),
        (">=", "at least (>=)"),
        ("<", "below (<)"),
        (">", "above (>)"),
        ("==", "equals (==)"),
        ("!=", "not equal (!=)"),
        ("in", "one of (a|b|c)"),
        ("is_true", "is yes"),
        ("is_false", "is no"),
    ], validators=[DataRequired()])
    value = StringField("Value", validators=[DataRequired(), Length(max=120)])
    description = StringField("Description", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Add rule")


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    kind = SelectField("Kind", choices=[("document", "Document"), ("scheme", "Scheme")],
                       validators=[DataRequired()])
    icon = StringField("Icon class (optional)", validators=[Optional(), Length(max=40)])
    submit = SubmitField("Add category")


class NotificationForm(FlaskForm):
    message = StringField("Message", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Broadcast to all users")
