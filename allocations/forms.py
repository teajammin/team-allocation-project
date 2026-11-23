from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordMixin,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

from .cohort import parse_cohort_csv
from .models import User


class BootstrapFormMixin:
    """Add Bootstrap's CSS classes to the input widgets of a form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class LogInForm(BootstrapFormMixin, AuthenticationForm):
    """Form to log in with a username and password."""


class PasswordForm(BootstrapFormMixin, PasswordChangeForm):
    """Form for a logged in user to change their own password."""

    # Replace Django's new_password1 and new_password2 fields with clearer names.
    new_password1 = None
    new_password2 = None
    new_password, new_password_confirmation = SetPasswordMixin.create_password_fields(
        label1='New password', label2='New password confirmation'
    )
    field_order = ['old_password', 'new_password', 'new_password_confirmation']

    def clean(self):
        self.validate_passwords('new_password', 'new_password_confirmation')
        self.validate_password_for_user(self.user, 'new_password_confirmation')
        return super().clean()

    def save(self, commit=True):
        return self.set_password_and_save(self.user, 'new_password', commit=commit)


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Form for a logged in user to edit their own profile."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class UserCreateForm(BootstrapFormMixin, UserCreationForm):
    """Form for a superuser to create a new user, including a password."""

    # Replace Django's password1 and password2 fields with clearer names.
    password1 = None
    password2 = None
    password, password_confirmation = SetPasswordMixin.create_password_fields()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']

    def validate_passwords(self, password1_field_name='password', password2_field_name='password_confirmation'):
        super().validate_passwords(password1_field_name, password2_field_name)

    def validate_password_for_user(self, user, password_field_name='password_confirmation'):
        super().validate_password_for_user(user, password_field_name)

    def set_password_and_save(self, user, password_field_name='password', commit=True):
        return super().set_password_and_save(user, password_field_name, commit)


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """Form for a superuser to update the details of any user."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']


class ProjectForm(BootstrapFormMixin, forms.Form):
    """Create a project with an initial, validated student cohort."""

    name = forms.CharField(max_length=200, label='Project name')
    cohort_file = forms.FileField(label='Cohort CSV')

    def clean_cohort_file(self):
        uploaded_file = self.cleaned_data['cohort_file']
        self.cleaned_data['students'] = parse_cohort_csv(uploaded_file)
        return uploaded_file


class CohortUploadForm(BootstrapFormMixin, forms.Form):
    """Validate a replacement cohort before changing the project."""

    cohort_file = forms.FileField(label='Cohort CSV')

    def clean_cohort_file(self):
        uploaded_file = self.cleaned_data['cohort_file']
        self.cleaned_data['students'] = parse_cohort_csv(uploaded_file)
        return uploaded_file


class AllocationForm(BootstrapFormMixin, forms.Form):
    """Configure team size and optional post-allocation policy checks."""

    min_team_size = forms.IntegerField(min_value=1, max_value=100, initial=4)
    max_team_size = forms.IntegerField(min_value=1, max_value=100, initial=5)
    check_gender = forms.BooleanField(
        required=False,
        label='Report gender representation findings',
    )
    check_attainment = forms.BooleanField(
        required=False,
        label='Report prior attainment findings',
    )
    max_spread = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        initial=20,
        label='Maximum within-team c-score spread',
    )

    def __init__(self, *args, students=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.students = students

    def clean(self):
        cleaned_data = super().clean()
        min_size = cleaned_data.get('min_team_size')
        max_size = cleaned_data.get('max_team_size')
        if min_size is not None and max_size is not None and min_size > max_size:
            self.add_error('max_team_size', 'Maximum team size must be at least the minimum.')

        if cleaned_data.get('check_attainment'):
            if cleaned_data.get('max_spread') is None:
                self.add_error('max_spread', 'Enter a maximum spread for the attainment check.')
            if self.students is not None and any(student.c_score is None for student in self.students):
                raise ValidationError(
                    'The attainment check requires a c-score for every student.'
                )
        return cleaned_data
